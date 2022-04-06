def my_short(i):
    i  = (i & 0xffff)
    if i&0x8000:
        i=-(((~i)&0xffff)+1)
    return i
