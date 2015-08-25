# Import all the libraries needed for this script
from bibliopixel.drivers.APA102 import *    # You will need to install BiblioPixel: https://github.com/ManiacalLabs/BiblioPixel
from bibliopixel import *
from bibliopixel.animation import *
from strip_animations import *              # This is an issue - you need to move this file to current directory
import bibliopixel.colors as colors
from datetime import datetime               # Standard should not have to install for date and time functions
from urllib2 import urlopen                 # Standard for parsin JSON from WeatherUnderGround
import json
import RPi.GPIO as GPIO, time, os           # Standard GPIO library for reading the light sensor

# Led locations 1 - 41 Left Side, 42 -119 Top, 120 - 176 Right Side
rightCorner = 119                           # Specific to my setup - pixel for top right and left corners 
leftCorner = 41 
topLength = rightCorner - leftCorner

# Display Variables                         # My preferences of colors and frame rates
FPS = 20
rainbow = [colors.Blue, colors.Turquoise, colors.Indigo, colors.Teal]
rain = [colors.Black, colors.Blue, colors.Black, colors.Black]
snow = [colors.Black, colors.White, colors.Black, colors.Black]
ptSunny = [colors.White, colors.Yellow, colors.White, colors.White]
ptCloudy = [colors.Yellow, colors.White, colors.Yellow, colors.Yellow]

#Load driver for the AllPixel
from bibliopixel.drivers.serial_driver import *
#set number of pixels & LED type here 
driver = DriverSerial(num = 164, type = LEDTYPE.APA102, c_order = ChannelOrder.BGR)

# This code from excellent Adafruit tutorial on reading a light sensor
# https://learn.adafruit.com/basic-resistor-sensor-reading-on-raspberry-pi/basic-photocell-reading
DEBUG = 1
GPIO.setmode(GPIO.BCM)  # Model for the Light Sensor
GPIO.setwarnings(False) # turns off warnings - obviously!
led = LEDStrip(driver)  # Model for the AllPixel
last_hour = 0
brightScale = 2

def RCtime (RCpin):     # From Adafruit - https://learn.adafruit.com/basic-resistor-sensor-reading-on-raspberry-pi/basic-photocell-reading
        reading = 0
        GPIO.setup(RCpin, GPIO.OUT)
        GPIO.output(RCpin, GPIO.LOW)
        time.sleep(0.1)
 
        GPIO.setup(RCpin, GPIO.IN)
        # This takes about 1 millisecond per loop cycle
        while (GPIO.input(RCpin) == GPIO.LOW):
                reading += 1
        return reading
try:
    while True:
        lightLevel = RCtime(18)     # Read RC timing using pin #18
        if (lightLevel < 400):
            led.setMasterBrightness(255)
        elif (lightLevel > 400 and lightLevel <= 4000):
            brightness = 255 - brightScale*(lightLevel/40)
            led.setMasterBrightness(brightness)
        else:
            led.setMasterBrightness(32)
        led.all_off()
        now = datetime.now()
        current_hour = now.hour
        if current_hour <= 5:       #Lights off in until 6am
            led.all_off()
        elif current_hour <= 18:   # During the day - show the weather
            if (current_hour != last_hour):
                last_hour = current_hour
                # Sign up for a free WeatherUnderground API account and put your key and location in the JSON request below
                # http://www.wunderground.com/weather/api
                req = urlopen('http://api.wunderground.com/api/xxxxxxxxx/forecast/q/State/City.json')
                parsed_json = json.load(req)
                pop = int(parsed_json['forecast']['txt_forecast']['forecastday'][0]['pop'])  # preciptiation
                high =int(parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit']) # high temp
                low =int(parsed_json['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit'])   # low temp
                icon = parsed_json['forecast']['simpleforecast']['forecastday'][0]['icon']                  # icon showing current conditions
                rainIndex = 164-45*int(pop)/100        # where to center the rain index on the right hand side        
                lowTempIndex = leftCorner+int(int(low)*topLength/100)  # where to center the low temp along the top 
                highTempIndex = leftCorner+int(int(high)*topLength/100) # where to center the low temp along the top 
                print 'Current chance of precipitation is {}.'.format(pop)
                print 'High temp today is {}.'.format(high)
                print 'Conditions today are {}.'.format(icon) 
                print 'LightLevel is {}.'.format(lightLevel)
            if int(pop) >> 0:
                led.fill(colors.Indigo,rainIndex-1,rainIndex+1)
            led.fill(colors.Red,highTempIndex-1,highTempIndex+1)
            led.fill(colors.Blue,lowTempIndex-1,lowTempIndex+1)
            if icon in ('cloudy','fog"'):                           # fog and cloudy static solid white
                led.fill(colors.White,0,leftCorner)  
            elif icon in ('clear','sunny'):                         # clear is static solid yellow
                led.fill(colors.Yellow,0,leftCorner)
            elif icon in ('rain','chancerain'):                     # rain is an animation of blue droplets
                anim = ColorPattern(led,rain,2,True,0,leftCorner)
                anim.run(amt = 2, fps = FPS, max_steps=100)         
            elif icon in ('tstorms','chancestorms','chancetstorms'): # thunderstorm animation is firefly lightning strikes                   
                anim = FireFlies(led,snow,width = 2,count = 2,start=0,end=41)
                anim.run(amt = 2, fps = FPS,max_steps=100)      
            elif icon in ('snow','sleet','flurries','chancesnow','chancesleet','chancesleet'):  # snow is an animation of falling white flakes
                anim = ColorPattern(led,snow,2,True,0,leftCorner)
                anim.run(amt = 2, fps = FPS,max_steps=100)
            elif icon in ('hazy','mostlycloudy','partlysunny'):     # static pattern of mainly white
                anim = ColorPattern(led,ptSunny,2,True,0,leftCorner)                 
                anim.run(amt = 0, fps = FPS, max_steps=1)                    
            elif icon in ('mostlysunny','partlycloudy'):            # static pattern of mainly yellow
                anim = ColorPattern(led,ptCloudy,2,True,0,leftCorner)
                anim.run(amt = 0, fps = FPS, max_steps=1)   
            else:                                                   # I want to notice if I missed something - all green
                led.fill(colors.Green,0,leftCorner)                 
            led.update()   
        elif current_hour <= 22:                                    # Switch over to the night-time mood lighting
            anim = ColorFade(led, rainbow, step=1)
            anim.run(fps = FPS, max_steps=900*len(rainbow))            
        elif current_hour <=23:                                     # Turn off the lights at 11
            led.all_off()
            led.update()
            break
except KeyboardInterrupt:
    led.all_off()
    led.update()