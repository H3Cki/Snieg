class fg:
    BLACK   = '\033[30m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'
    RESET   = '\033[39m'

class bg:
    BLACK   = '\033[40m'
    RED     = '\033[41m'
    GREEN   = '\033[42m'
    YELLOW  = '\033[43m'
    BLUE    = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN    = '\033[46m'
    WHITE   = '\033[47m'
    RESET   = '\033[49m'

class style:
    BRIGHT    = '\033[1m'
    DIM       = '\033[2m'
    NORMAL    = '\033[22m'
    RESET_ALL = '\033[0m'

COLORIZE = True

def get_colorize():
    return COLORIZE

def toggle_colorize(v):
    global COLORIZE
    COLORIZE = v

def bright(func):
    def bright_wrapper(text, *args, **kwargs):
        if COLORIZE:
            return func(kwargs.get('style', style.BRIGHT) + text + style.RESET_ALL, *args, **kwargs)
        else:
            return text
    return bright_wrapper

@bright
def red(text, **kwargs):
    return fg.RED + text + fg.RESET

@bright
def green(text, **kwargs):
    return fg.GREEN + text + fg.RESET

@bright
def yellow(text, **kwargs):
    return fg.YELLOW + text + fg.RESET

@bright
def white(text, **kwargs):
    return fg.WHITE + text + fg.RESET

@bright
def cyan(text, **kwargs):
    return fg.CYAN + text + fg.RESET

@bright
def magenta(text, **kwargs):
    return fg.MAGENTA + text + fg.RESET

@bright
def black(text, **kwargs):
    return fg.BLACK + text + fg.RESET


@bright
def blue(text, **kwargs):
    return fg.BLUE + text + fg.RESET


#BG



def pad(func):
    def pad_wrapper(text, *args, **kwargs):
        padding = kwargs.get('pad')
        pad_char = ' ' * kwargs.get('padn', 1)
        if padding == True:
            text = pad_char + text + pad_char
        elif padding == 'left':
            text = pad_char + text
        elif padding == 'right':
            text = text + pad_char
        return func(text, *args, **kwargs)
    return pad_wrapper

def blackify(func):
    def black_wrapper(text, *args, **kwargs):
        return func(black(text, **kwargs), *args, **kwargs)
    return black_wrapper

@pad
@bright
@blackify
def bg_red(text, **kwargs):
    return bg.RED + text + bg.RESET

@pad
@bright
@blackify
def bg_green(text, **kwargs):
    
    return bg.GREEN + text + bg.RESET

@pad
@bright
@blackify
def bg_yellow(text, **kwargs):
    
    return bg.YELLOW + text + bg.RESET

@pad
@bright
@blackify
def bg_white(text, **kwargs):
    
    return bg.WHITE + text + bg.RESET

@pad
@bright
@blackify
def bg_cyan(text, **kwargs):
    
    return bg.CYAN + text + bg.RESET
    
    
def custom(text, fg='', fg_reset=True, bg='', bg_reset=True):
    return fg + bg + text + fg_reset + bg_reset
