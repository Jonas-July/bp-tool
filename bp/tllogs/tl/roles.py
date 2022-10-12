

def does_log_belong_to_group(group, log):
    return log.group == group

def is_log_of_tl(user, log):
    author = log.tl
    return user.tl == author