"""
Django management command to send reminders that are due or approaching due date.

Usage:
    python manage.py send_due_reminders                    # Send reminders due today
    python manage.py send_due_reminders --days 7           # Send reminders due within 7 days
    python manage.py send_due_reminders --days 3 --dry-run # Preview without sending
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from reminders.models import Reminder
from core.whatsapp import send_sms, send_whatsapp_message


def _build_reminder_message(r) -> str:
    """Build a professional reminder message."""
    from django.conf import settings as conf
    
    customer = r.vehicle.customer
    v = r.vehicle
    shop = getattr(conf, "SHOP_NAME", "Sanjay Auto Works")
    phone = getattr(conf, "SHOP_PHONE", "")
    reminder_type = r.get_reminder_type_display()
    due_date = r.due_date.strftime('%d %b %Y') if r.due_date else 'soon'
    
    return (
        f"Dear {customer.name},\n\n"
        f"This is a service reminder from {shop}.\n\n"
        f"Your vehicle {v.registration_number} ({v.make} {v.model}) is due for {reminder_type} on {due_date}.\n\n"
        f"Please contact us at your earliest convenience to schedule an appointment:\n\n"
        f"Phone: {phone}\n\n"
        f"Thank you for your business.\n\n"
        f"{shop}"
    )


class Command(BaseCommand):
    help = "Send reminders that are due or approaching due date"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Send reminders due within N days (default: 0 = today only)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview reminders without sending'
        )
        parser.add_argument(
            '--channel',
            type=str,
            choices=['sms', 'whatsapp'],
            help='Override channel (defaults to reminder channel preference)'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        channel_override = options.get('channel')
        
        today = timezone.now().date()
        cutoff = today + timedelta(days=days)
        
        # Get pending reminders that are due within the window
        reminders = Reminder.objects.filter(
            status='pending',
            due_date__lte=cutoff,
        ).select_related('vehicle__customer')
        
        if not reminders.exists():
            self.stdout.write(self.style.SUCCESS('✓ No reminders to send.'))
            return
        
        sent = 0
        failed = 0
        
        for r in reminders:
            try:
                channel = channel_override or r.channel
                message = _build_reminder_message(r)
                phone = r.vehicle.customer.phone
                
                if not phone:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Skipped {r}: No phone number on file'
                        )
                    )
                    failed += 1
                    continue
                
                # Show preview
                self.stdout.write(f'\n📱 {r.get_reminder_type_display()} - {r.vehicle.registration_number}')
                self.stdout.write(f'   Customer: {r.vehicle.customer.name}')
                self.stdout.write(f'   Due: {r.due_date.strftime("%d %b %Y")}')
                self.stdout.write(f'   Channel: {channel.upper()}')
                self.stdout.write(f'   Phone: {phone}')
                self.stdout.write(f'   Message preview: {message[:100]}...')
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('   [DRY RUN - NOT SENT]'))
                    sent += 1
                    continue
                
                # Send the reminder
                if channel == 'sms':
                    ok, reason = send_sms(phone, message)
                elif channel == 'whatsapp':
                    ok, reason = send_whatsapp_message(phone, message)
                else:
                    ok, reason = False, f"Unknown channel: {channel}"
                
                if ok:
                    # Mark as sent
                    r.status = 'sent'
                    r.sent_at = timezone.now()
                    r.save()
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Sent via {channel.upper()}'))
                    sent += 1
                else:
                    self.stdout.write(self.style.ERROR(f'   ✗ Failed: {reason}'))
                    failed += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ Error: {str(e)}'))
                failed += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would send {sent} reminders'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Sent {sent} reminders'))
        
        if failed:
            self.stdout.write(self.style.WARNING(f'⚠ {failed} reminders failed'))
