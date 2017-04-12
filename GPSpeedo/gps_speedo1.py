#! /usr/bin/env python

from __future__   import division
#from serial       import Serial
import datetime, sys


# Notes:
#
# http://aprs.gids.nl/nmea/
# https://rl.se/gprmc
#

"""
$GPRMC

Recommended minimum specific GPS/Transit data

eg1. $GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62
eg2. $GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68


           225446       Time of fix 22:54:46 UTC
           A            Navigation receiver warning A = OK, V = warning
           4916.45,N    Latitude 49 deg. 16.45 min North
           12311.12,W   Longitude 123 deg. 11.12 min West
           000.5        Speed over ground, Knots
           054.7        Course Made Good, True
           191194       Date of fix  19 November 1994
           020.3,E      Magnetic variation 20.3 deg East
           *68          mandatory checksum


eg3. $GPRMC,220516,A,5133.82,N,00042.24,W,173.8,231.8,130694,004.2,W*70
              1    2    3    4    5     6    7    8      9     10  11 12


      1   220516     Time Stamp
      2   A          validity - A-ok, V-invalid
      3   5133.82    current Latitude
      4   N          North/South
      5   00042.24   current Longitude
      6   W          East/West
      7   173.8      Speed in knots
      8   231.8      True course
      9   130694     Date Stamp
      10  004.2      Variation
      11  W          East/West
      12  *70        checksum


eg4. $GPRMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,ddmmyy,x.x,a*hh
1    = UTC of position fix
2    = Data status (V=navigation receiver warning)
3    = Latitude of fix
4    = N or S
5    = Longitude of fix
6    = E or W
7    = Speed over ground in knots
8    = Track made good in degrees True
9    = UT date
10   = Magnetic variation degrees (Easterly var. subtracts from true course)
11   = E or W
12   = Checksum
"""

# $GPRMC,001225,A,2832.1834,N,08101.0536,W,12,25,251211,1.2,E,A*03

class GPSreader():
  
  FMT = "%H:%M:%S.%f"
  
  
  _GPRMC_pattern  = { 'TIMESTAMP':1, 'STATUS':2, 'LAT':3, 'LAT_N_S':4, 'LOG':5, 'LOG_E_W':6, 'SPEED':7,
                      'COURSE':8, 'DATE':9,  'VAR':10, 'VAR_E_W':11, 'CHKS':12, 'LENGTH':13}
  
    
  def __init__(self):
    self._speed        = 0
    self._latitude     = 0
    self._longitude    = 0
    self._timestamp    = ""
    self._gps_raw      = {}      

  
  @property
  def speed(self):
    return self._speed
    
  
  @property  
  def latitude(self):
    return self._latitude
    
  
  @property
  def lognitude(self):
    return self._lognitude
    
  @property
  def timestamp(self):
    return self._timestamp
  
  
  def break_gps_str(self, gps_str):
    
    gps_split = gps_str.split(',')
    self._gps_raw = {}
    
    if len(gps_split) == self._GPRMC_pattern['LENGTH']:
      self._gps_raw = {key:(gps_split[self._GPRMC_pattern[key]] if key != 'LENGTH' else 0) for key in self._GPRMC_pattern}
      self._gps_raw.pop('LENGTH')
    
    return self._gps_raw
      

    
  def gps2dec(self, coord_text):
    
    try:
      major, minor = coord_text.split('.')  
      degrees  = int(major) // 100
      minutes  = (int(major) % 100 + float('0.' + minor)) / 60
      return  degrees + minutes
    except:
      return None
          


  def gps_time2obj(self, time_text):
    
    major, minor  = time_text.split('.')
    hours      = int(major) // 10000
    minutes     = (int(major) % 10000) // 100
    sec        = int(major) % 100
    ssec      = int(minor)
    time_str     = "{0}:{1}:{2}.{3}".format(hours, minutes, sec, ssec) 
    time_obj    = datetime.datetime.strptime(time_str, self.FMT)
    
    return time_obj
    
    
  def speed2speed(self, speed):
    try:
      self.speed = float(speed) * 1.852
    except Exception as e:
      self.speed = -1
      raise ValueError("Unable to get speed value due to exception: {0}".format(str(e)))
      
    return self.speed
      
    
  def get_coords(self, lat, lon, time):
    self.start_coords  = self.stop_coords
    self.stop_coords  = {'LAT':self.gps2dec(lat), 'LON':self.gps2dec(lon), 'TIME':time}
    time_diff  = self.gps_time2obj(self.stop_coords['TIME'])\
          - self.gps_time2obj(self.start_coords['TIME'])
          
    self.time_diff = time_diff.seconds                    
    if not self.time_diff:
      return False
    return self._calc_speed()
    
    
speedometer = GPSreader()

  
#rfcomm    = Serial('/dev/rfcomm0')
#rfcomm.flush()  



print(speedometer.break_gps_str("$GPRMC,205920.00,A,5320.20886,N,00618.25299,W,0.072,,120417,,,A*60"))


"""
while True:
  gps_line = rfcomm.readline()
  if 'GPGGA' in gps_line:
    
    line_split = gps_line.split(',')
    time_stamp, lat, lon = line_split[1].strip(), line_split[2].strip(), line_split[4].strip()
    
    if speedometer.get_coords(lat, lon, time_stamp):
      out_text = "{0} -> SPEED: {1:6.2f} km/h {2:6.2f} m/s\tLAT: {3} LON: {4}\tTIME: {5}".format(time_stamp, speedometer.speed_kmh, speedometer.speed_ms, lat, lon, speedometer.time_diff) 
      print out_text
    
  elif 'GPRMC' in gps_line:
    line_split = gps_line.split(',')
    time_stamp, lat, lon ,speed = line_split[1].strip(), line_split[3].strip(), line_split[5].strip(), line_split[7].strip()
    print time_stamp, lat, lon ,str(float(speed) * 1.852) + " km/h"
    
    
      
    #f.write(out_text + '\n')   
  rfcomm.flush()  
"""