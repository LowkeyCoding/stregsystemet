import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.db.models import Count, F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def make_active_productlist_query(queryset):
    now = timezone.now()
    # Create a query for the set of products that MIGHT be active. Might
    # because they can be out of stock. Which we compute later
    active_candidates = (
        queryset
            .filter(
            Q(active=True)
            & (Q(deactivate_date=None) | Q(deactivate_date__gte=now)))
    )
    # This query selects all the candidates that are out of stock.
    candidates_out_of_stock = (
        active_candidates
            .filter(sale__timestamp__gt=F("start_date"))
            .annotate(c=Count("sale__id"))
            .filter(c__gte=F("quantity"))
            .values("id")
    )
    # We can now create a query that selects all the candidates which are not
    # out of stock.
    return (
        active_candidates
            .exclude(
            Q(start_date__isnull=False)
            & Q(id__in=candidates_out_of_stock)))


def make_inactive_productlist_query(queryset):
    now = timezone.now()
    # Create a query of things are definitively inactive. Some of the ones
    # filtered here might be out of stock, but we include that later.
    inactive_candidates = (
        queryset
            .exclude(
            Q(active=True)
            & (Q(deactivate_date=None) | Q(deactivate_date__gte=now)))
            .values("id")
    )
    inactive_out_of_stock = (
        queryset
            .filter(sale__timestamp__gt=F("start_date"))
            .annotate(c=Count("sale__id"))
            .filter(c__gte=F("quantity"))
            .values("id")
    )
    return (
        queryset
            .filter(
            Q(id__in=inactive_candidates)
            | Q(id__in=inactive_out_of_stock))
    )


def make_room_specific_query(room):
    return (
            Q(rooms__id=room) | Q(rooms=None)
    )


def date_to_midnight(date):
    """
    Converts a datetime.date to a datetime of the same date at midnight.

    :param date: date to convert
    :return: the date as a timezone aware datetime at midnight
    """
    return timezone.make_aware(timezone.datetime(date.year, date.month, date.day, 0, 0))

def send_payment_mail(member, amount):
    formatted_amount = "{0:.2f}".format(amount / 100.0)

    html = f"""
    <html>
        <body>
            <p>Hej {member.firstname}!<br><br>
               Vi har indsat {formatted_amount} stregdollars på din konto: "{member.username}". <br><br>
               Hvis du ikke ønsker at modtage flere mails som denne kan du skrive en mail til: <a href="mailto:treo@fklub.dk?Subject=Klage" target="_top">fklub@elefsennet.dk</a><br><br>
               Mvh,<br>
               TREOen<br>
               ====================================================================<br>
               Hello {member.firstname}!<br><br>
               We've inserted {formatted_amount} stregdollars on your account: "{member.username}". <br><br>
               If you do not desire to receive any more mails of this sort, please file a complaint to: <a href="mailto:treo@fklub.dk?Subject=Klage" target="_top">fklub@elefsennet.dk</a><br><br>
               Kind regards,<br>
               TREOen
        </body>
    </html>
    """

    send_mail(member.email, 'Stregsystem payment', html)

def send_sign_mail(member):
    html = f"""
    <html>
        <body>
            Welcome {member.Name}<br><br>
            You are now a member of F-Klubben.<br><br>
            F-Klubben will be hosting various events through out the semester.<br>
            These events include our annual events like the Christmas party (F-julefrokost)<br>
            , the sports day (F-sportsdag), the cabin trip (Fyttetur) and so much <a href="http://www.fklub.dk/aktiviteter/start">more</a>!<br><br>
            The perhaps most important event is the Friday bread (FredagsFranskbrød)<br>
            each Wednesday at 10.00 o'clock in the cafeterie, where there will be 2 free<br>
            slices of bread for each F-Klub member.<br><br>
            F-Klubben also has some refrigerators with different beverages located in<br>
            cluster 5. These can be bought through the <a href="http://www.fklub.dk/treo/stregsystem">Stregsystem</a>.<br><br>
            To follow the events in F-Klubben, you can follow us on our Face page: <a href="https://www.facebook.com/fklub">F-Klubben</a>, <br>
            keep an eye out for the posters we put up, and the monitors we have placed in<br>
            cluster 5 and the cafeteria.<br><br>
            Best regards,<br>
            TREOen<br>
            <a href="https://www.facebook.com/groups/721831544500061">Fembers for F-Klubben members to F-Klubben members</a><br>
            <a href="https://www.facebook.com/fklub">F-Klubben on Facebook, follow announcements and events</a>
        </body>
    </html>
    """
    send_mail(member.email, 'Welcome to F-Klubben', html) 


def send_mail(email_addr, subject, msg_html_body):
    msg = MIMEMultipart()
    msg['From'] = 'treo@fklub.dk'
    msg['To'] = email_addr
    msg['Subject'] = subject

    msg.attach(MIMEText(msg_html_body, 'html'))

    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', email_addr, msg.as_string())
    except Exception as e:
        logger.error(str(e))
