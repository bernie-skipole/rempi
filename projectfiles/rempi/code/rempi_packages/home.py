
import math

from skipole import FailPage, GoTo, ValidateError, ServerError




def index_page(skicall):
    "Fills in the public index page"

    skicall.page_data['headingtext', 'large_text'] = "REMPI01"

    skicall.page_data['intro', 'large_text'] = "You are connected to Raspberry Pi - REMPI01"

    redis = skicall.proj_data['redis']

    target_name = redis.get("rempi01_target_name")
    target_ra = redis.get("rempi01_target_ra")
    target_dec = redis.get("rempi01_target_dec")
    target_alt = redis.get("rempi01_target_alt")
    target_az = redis.get("rempi01_target_az")
    target_alt_speed = redis.get("rempi01_target_alt_speed")
    target_az_speed = redis.get("rempi01_target_az_speed")

    target_text = ""

    if target_name:
        target_text += "\nTarget name : " + target_name.decode("utf-8")

    if target_ra and target_dec:
        rahr, ramin, rasec, decsign, decdeg, decmin, decsec = _ra_dec_conversion(float(target_ra.decode("utf-8")), float(target_dec.decode("utf-8")))
        target_text += "\nTarget RA :  %s h  %s m " % ( rahr, ramin ) 
        target_text += "{:1.3f} s".format(rasec)
        target_text += "\nTarget DEC :  %s %s d  %s m " % ( decsign, decdeg, decmin )
        target_text += "{:1.3f} s".format(decsec)

    if target_alt:
        target_text += "\nTarget ALT : " + target_alt.decode("utf-8")

    if target_az:
        target_text += "\nTarget AZ : " + target_az.decode("utf-8")

    if target_alt_speed:
        target_text += "\nTarget ALT speed : " + target_alt_speed.decode("utf-8")

    if target_az_speed:
        target_text += "\nTarget AZ speed : " + target_az_speed.decode("utf-8")

    if target_text:
        skicall.page_data['target', 'para_text'] = target_text


def _ra_dec_conversion(ra, dec):
    """Given ra and dec in degrees, convert to (rahr, ramin, rasec, decsign, decdeg, decmin, decsec)
       where decsign is a string, either '+' or '-'"""
    # get ra, dec in hms, dms
    rahr = math.floor(ra / 15.0)
    if not rahr:
        ra_remainder = ra
    else:
        ra_remainder = math.fmod(ra, rahr*15.0)
    if not ra_remainder:
        ramin = 0
        rasec = 0.0
    else:
        ramin = math.floor(ra_remainder * 4)
        ra_remainder = math.fmod(ra_remainder, 1.0/4.0)
        if not ra_remainder:
            rasec = 0.0
        else:
            rasec = ra_remainder * 240

    if "{:2.1f}".format(rasec) == "60.0":
        rasec = 0
        ramin += 1
    if ramin == 60:
        ramin = 0
        rahr += 1
    if rahr == 24:
        rahr = 0

    absdeg = math.fabs(dec)
    decdeg = math.floor(absdeg)
    if not decdeg:
        dec_remainder = absdeg
    else:
        dec_remainder = math.fmod(absdeg, decdeg)
    if not dec_remainder:
        decmin = 0
        decsec = 0.0
    else:
        decmin = math.floor(dec_remainder * 60)
        dec_remainder = math.fmod(dec_remainder, 1.0/60.0)
        if not dec_remainder:
            decsec = 0.0
        else:
            decsec = dec_remainder * 3600

    if "{:2.1f}".format(decsec) == "60.0":
        decsec = 0
        decmin += 1
    if decmin == 60:
        decmin = 0
        decdeg += 1

    if dec >= 0.0:
        decsign = '+'
    else:
        decsign = '-'
    return (rahr, ramin, rasec, decsign, decdeg, decmin, decsec)



