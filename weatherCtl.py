import argparse
from collections import defaultdict
from lxml import etree
from urllib import request

sourceLink = 'https://www.yr.no/place/Norway/S%C3%B8r-Tr%C3%B8ndelag/Trondheim/Trondheim/forecast.xml'
color_mode = False


# Organize flags and arguments
def get_options():
    parser = argparse.ArgumentParser(description='Display command line weather data')
    parser.add_argument(
        '--custom',
        action='store',
        help='Specify custom link (only yr.no supported)',
    )
    parser.add_argument(
        '--time',
        action='store',
        default=3,
        help='Specify number of days (default = 3)',
    )
    parser.add_argument(
        '--next',
        action='store_true',
        help='Display only the next non-active forecast (default = False)',
    )
    parser.add_argument(
        '-n',
        action='store_true',
        help='Same as --next',
    )
    parser.add_argument(
        '--ret',
        action='store_true',
        help='Return next non-active forecast, will not print anything (default=False)',
    )
    parser.add_argument(
        '--color',
        action='store_true',
        help = 'Output text in color (default = False)'
    )
    return parser.parse_args()


# Process given arguments
def controller(root, args):
    if args.custom:  # Set source url
        global sourceLink
        sourceLink = args.custom
    if args.color:
        global color_mode
        color_mode = True
    if args.next or args.n:
        disp_next(root)  # Display only the next period which has not begun
    elif args.ret:
        return_next(root)  # Same as previous, but returns result instead of printing directly
    else:
        disp_multi(root, int(args.time))  # Display the next x days


# Return result for disp_next, for use in other programs, such as lemonbar
def return_next(root):
    forecast = root.iterchildren(tag='forecast')
    next_time = list(list(forecast)[0].iterchildren(tag='tabular'))[0].getchildren()[1]
    return get_period_data(next_time)


# Display only the next forecast
def disp_next(root):
    print(return_next(root))


# Display long term forecast
def disp_multi(root, n):
    forecast = root.iterchildren(tag='forecast')
    time_list = list(list(forecast)[0].iterchildren(tag='tabular'))[0].getchildren()
    # Group by date
    dates = defaultdict(list)
    dates_select = set()
    for interval in time_list:
        start_date = interval.attrib['from'].split('T')[0]
        dates[start_date].append(interval)
        dates_select.add(start_date)
    # Select specified intervals
    selection = sorted(list(dates_select))[:n]
    # Display weather for each date
    for date in dates:
        if date in selection:
            print(date)
            for element in dates[date]:
                print(get_period_data(element))


def get_period_data(timestep):
    time = timestep.attrib['from'].split('T')[1][:5]
    temp = (list(timestep.iterchildren(tag='temperature'))[0].attrib['value'])
    symbol = list(timestep.iterchildren(tag='symbol'))[0].attrib['name']
    precip = list(timestep.iterchildren(tag='precipitation'))[0].attrib['value'] + 'mm'
    wind = list(timestep.iterchildren(tag='windSpeed'))[0].attrib['name']
    endchar = ''
    if color_mode:
        time, temp, symbol, precip, wind = add_colors(time, temp, symbol, precip, wind)
        endchar = '\033[0m'
    return '{0:5}  {1:8}  {2:20}  {3:5}  {4:20}  {5:5}'.format(
        time, temp + 'C', symbol, precip, wind, endchar)


def add_colors(time, temp, symbol, precip, wind):
    # Colorscheme, using ANSI
    color_red = '\033[31m'
    color_yellow = '\033[33m'
    color_green = '\033[32m'
    color_blue = '\033[34m'
    color_cyan = '\033[36m'
    color_white = '\033[37m'
    color_grey = '\033[30;1m'
    color_reset = '\033[0m'
    # Keep time default-colored
    time = color_reset + time
    # Determine temperature color based on value
    temp = int(temp)
    if temp >= 20:
        temp = color_red + str(temp)
    elif temp >= 10:
        temp = color_yellow + str(temp)
    elif temp >= 0:
        temp = color_green + str(temp)
    else:
        temp = color_cyan + str(temp)
    # Symbol-text coloring
    clear = ['Clear sky', 'Fair']
    rain = ['Light rain showers', 'Rain showers', 'Heavy rain showers', 'Light rain', 'Rain', 'Heavy rain']
    snow = ['Light snow showers', 'Snow showers', 'Heavy snow showers', 'Light snow', 'Snow', 'Heavy snow']
    cloudy = ['Cloudy', 'Partly cloudy']
    if symbol in clear:
        symbol = color_yellow + symbol
    elif symbol in rain:
        symbol = color_blue + symbol
    elif symbol in snow:
        symbol = color_cyan + symbol
    elif symbol in cloudy:
        symbol = color_white + symbol
    # Rain coloring
    precip = float(precip[:-2])
    if precip >= 10:
        precip = color_red + str(precip)
    elif precip > 0:
        precip = color_blue + str(precip)
    else:
        precip = color_green + str(precip)
    # Wind coloring
    wind = color_reset + wind
    return time, temp, symbol, precip, wind

def main():
    root = etree.parse(request.urlopen(sourceLink, timeout=3)).getroot()
    args = get_options()
    controller(root, args)
    # TODO: add short version arguments
    # TODO: Add proper error checking


if __name__ == '__main__':
    main()
