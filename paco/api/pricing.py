
_price_per_m = 0.0075

def get_price(distance, box_size, weight, fragile=False):
    box_size_mult_dict = {
        1: 1.0,
        2: 1.2,
        3: 1.3
    }

    weight_mult_dict = [0, 1, 1.0, 1.3]

    '''
        {
        1: 1.0,
        2: 1.2,
        3: 1.3
    }
    '''

    weight_mult = 0

    if weight > 11:
        weight_mult = weight_mult_dict[3]
    elif weight > 5:
        weight_mult = weight_mult_dict[2],
    else:
        weight_mult = weight_mult_dict[1]

    box_size_mult = box_size_mult_dict[box_size]

    fragile_mult = 1.5 if fragile else 1

    return int(_price_per_m * weight_mult * box_size_mult * fragile_mult * float(distance))
