from functools import wraps

from flask import jsonify

from blacklist.models.blacklist import Role

"""
    if current_user.role not in [Role.ADMIN]:
        flask.flash('You need to be administrator for this action', 'danger')
        return flask.redirect(flask.url_for('user.login'))
"""


class Acl(object):

    @staticmethod
    def roles_to_list(roles):
        ret = []
        for role in roles:
            ret.append(role.id)
        return ret

    @staticmethod
    def get_user_roles(user):
        roles = Acl.roles_to_list(user.roles)
        if not user.is_authenticated():
            roles.append(Role.GUEST)

        return roles

    @staticmethod
    def validate_path(allowed, user):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not set(Acl.get_user_roles(user)).isdisjoint(allowed):
                    # continue
                    return f(*args, **kwargs)
                else:
                    # Unauthorized
                    return jsonify({'message': 'Unauthorized access (Wrong API token)'}), 401

            return decorated_function

        return decorator

    @staticmethod
    def validate(allowed, user):
        return not set(Acl.roles_to_list(user.roles)).isdisjoint(allowed)
