
def get_price(distance, box_size, weight, fragile=False):
    box_size_mult_dict = {
        1: 1,
        2: 1.2,
        3: 1.3
    }

    weight_mult_dict = {
        1: 1,
        2: 1.2,
        3: 1.3
    }

    weight_mult = 0

    if weight > 11:
        weight_mult = weight_mult_dict[3]
    elif weight > 5:
        weight_mult = weight_mult_dict[2],
    else:
        weight_mult = weight_mult_dict[1]

    box_size_mult = box_size_mult_dict[box_size]

    fragile_mult = 1.5 if fragile else 1

    return int(0.01 * weight_mult * box_size_mult * fragile_mult * distance)
