
class ParamCheckException(Exception):
    pass


class Validators(object):

    @staticmethod
    def param_check(configs, params):
        if configs is None or len(configs) == 0:
            raise ParamCheckException('Configs parameter cannot be empty')
        if params is None or len(params) == 0:
            raise ParamCheckException('No valid parameters specified')

        ret = {}
        for config in configs:
            if config['name'] not in params:
                if 'optional' in config and config['optional']:
                    ret[config['name']] = None
                else:
                    raise ParamCheckException('Required parameter {} is missing'.format(config['name']))
            else:
                # We have a param, lets check it
                if 'type':
                    t = type(params[config['name']])
                    if t is unicode:
                        t = str

                    if type(config['type']) is list:
                        if t not in config['type']:
                            raise ParamCheckException(
                                'Parameter {} has wrong format ({} not in [{}])'.format(
                                    config['name'],
                                    t,
                                    config['type']
                                )
                            )
                        ret[config['name']] = params[config['name']]

                    elif t is not config['type']:
                        # we gonna cast it to that type
                        try:
                            ret[config['name']] = config['type'](params[config['name']])
                        except ValueError:
                            raise ParamCheckException(
                                'Failed to cast {} from {} to {}'.format(config['name'], t, config['type']))
                    else:
                        ret[config['name']] = params[config['name']]

                else:
                    ret[config['name']] = params[config['name']]

                if 'mlen' in config:
                    if type(params[config['name']]) is str:
                        if config['mlen'] < len(params[config['name']]):
                            raise ParamCheckException('Parameter {} is too long ({} > {})'.format(
                                config['name'], len(params[config['name']]), config['mlen']))
                    elif type(params[config['name']]) is int:
                        if config['mlen'] < params[config['name']]:
                            raise ParamCheckException('Parameter {} is too big ({} > {})'.format(
                                config['name'], params[config['name']], config['mlen']))

        return ret
