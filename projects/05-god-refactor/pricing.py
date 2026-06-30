def process_order(items, customer_type, coupon):
    # compute subtotal
    subtotal = 0
    for it in items:
        subtotal = subtotal + it["price"] * it["qty"]

    # figure out discount based on customer type
    if customer_type == "vip":
        after_discount = subtotal - subtotal * 0.10
    else:
        if customer_type == "member":
            after_discount = subtotal - subtotal * 0.05
        else:
            after_discount = subtotal

    # apply coupon
    if coupon is not None:
        if coupon == "SAVE5":
            after_coupon = after_discount - 5
            if after_coupon < 0:
                after_coupon = 0
            free_ship = False
        elif coupon == "FREESHIP":
            after_coupon = after_discount
            free_ship = True
        else:
            after_coupon = after_discount
            free_ship = False
    else:
        after_coupon = after_discount
        free_ship = False

    # shipping
    if free_ship:
        shipping = 0
    else:
        if after_coupon >= 100:
            shipping = 0
        else:
            shipping = 10

    # tax
    tax = after_coupon * 0.08

    # total
    total = after_coupon + tax + shipping

    result = {}
    result["subtotal"] = round(subtotal, 2)
    result["discount"] = round(subtotal - after_coupon, 2)
    result["tax"] = round(tax, 2)
    result["shipping"] = round(shipping, 2)
    result["total"] = round(total, 2)
    return result
