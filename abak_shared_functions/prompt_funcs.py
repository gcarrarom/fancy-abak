def ask_yn(yn_question, default='n'):
    tries = 0
    while True:
        response = input("%s (y/n)" % (yn_question))
        tries = tries + 1
        if response in  ['y', 'n']:
            break
        elif tries > 2:
            response = default
            break
    return True if response == 'y' else False