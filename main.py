import configparser
import os
import requests


def main():
    msgs = {'info': '[INFO]: ',
            'input': '[INPUT]: ',
            'error': '[ERROR]: '}
    print(msgs['info'] + 'Parsing config...')
    params = parse_config('config.ini')
    print(msgs['info'] + 'Ready to go!')
    while True:
        user_id = input(msgs['input'] + 'Enter user id/screen name '
                                        '(type "exit" to quit): ')
        if user_id == 'exit':
            break
        request_params = {'user_ids': user_id, 'v': params['api_version'],
                          'access_token': params['token']}
        response = send_get_request(params['link'], params['main_method'],
                                    request_params)
        if response.status_code != 200:
            print(msgs['error'] + 'Can\'t get proper response')
            print(msgs['error'] + 'Response code: ' +
                  str(response.status_code))
            continue
        content = response.json()
        if 'error' in content:
            err_content = content['error']
            print_error_msg(msgs['error'], err_content['error_code'],
                            err_content['error_msg'])
            continue
        if len(content['response']) == 0:
            print(msgs['error'] + 'Wrong id were given (probably 0 which '
                                  'refer to self account)')
            continue
        user_info = content['response'][0]
        print_user_info(msgs['info'], user_info)
        if user_info['first_name'] == 'DELETED' or user_info['is_closed']:
            print(msgs['info'] + 'There\'s no enabled options for '
                                 'that profile, since it is closed '
                                 'or have been deleted')
            continue
        else:
            print_enabled_options(msgs['info'], params['options'])
            while True:
                choose = input(msgs['input'] + 'Type option number '
                                               '(use 0 to continue): ')
                while not (choose.isdigit() and
                           int(choose) <= len(params['options'])):
                    print(msgs['error'] + 'Incorrect input!')
                    choose = input(msgs['input'] + 'Type option number '
                                                   '(use 0 to continue): ')
                if choose == '0':
                    break
                request_params = {'user_id': user_info['id'],
                                  'access_token': params['token'],
                                  'v': params['api_version']}
                response = send_get_request(params['link'], 
                                            params['options'][int(choose) - 1]
                                            ['method'],
                                            request_params)
                if response.status_code != 200:
                    print(msgs['error'] + 'Can\'t get proper response')
                    print(msgs['error'] + 'Response code: ' +
                          str(response.status_code))
                    continue
                content = response.json()
                if 'error' in content:
                    err_content = content['error']
                    print_error_msg(msgs['error'], err_content['error_code'],
                                    err_content['error_msg'])

                parse_option_response(params['options'][int(choose) - 1],
                                      msgs, content, params)


def parse_config(config_file_name):
    config_path = os.path.join(os.getcwd(), config_file_name)
    if not os.path.exists(config_path):
        raise FileNotFoundError('No config file found!')
    info = {}
    cp = configparser.ConfigParser()
    cp.read(config_path)
    info['api_version'] = cp.get('API', 'ver')
    info['link'] = cp.get('API', 'req_link')
    info['main_method'] = cp.get('API', 'main_method')
    info['token'] = cp.get('App', 'token')
    option_names = {}
    options = []
    for k, v in cp.items('MenuItems'):
        option_names[k] = v
    for k, v in cp.items('Methods'):
        options.append({'name': option_names[k], 'method': v})
    info['options'] = options
    return info


def send_get_request(link, method, params):
    return requests.get(link + method, params=params)


def print_error_msg(prefix, code, msg):
    print(prefix + 'Code: ' + code.__str__())
    print(prefix + 'Message: ' + msg)


def print_user_info(prefix, user_info):
    lines = [(prefix + 'User ID').ljust(24) + user_info['id'].__str__(),
             (prefix + 'First name').ljust(24) + user_info['first_name'],
             (prefix + 'Last name').ljust(24) + user_info['last_name']]
    length = len(max(lines, key=len))
    print('=' * length)
    print('\n'.join(lines))
    print('=' * length)


def print_enabled_options(prefix, options):
    print(prefix + 'Enabled options:')
    for i in range(len(options)):
        print('{}[{}] {}'.format(prefix, i + 1, options[i]['name']))


def parse_option_response(option, msgs, content, params):
    if option['method'] == 'friends.get':
        get_friends_info(msgs, content, params)
    elif option['method'] == 'photos.getAlbums':
        print_albums_info(msgs, content['response']['items'])
    else:
        print(content)
        print('To realise this type of output - edit function '
              'named parse_option_response')


def get_friends_info(msgs, content, params):
    ids = [str(u_id) for u_id in content['response']['items']]
    parts = divide_chunks(ids, 250)
    friends = []
    counter = 1
    max_len = 0
    for part in parts:
        request_params = {'user_ids': ','.join(part),
                          'v': params['api_version'],
                          'access_token': params['token']}
        response = send_get_request(params['link'], params['main_method'],
                                    request_params)
        if response.status_code != 200:
            print(msgs['error'] + 'Can\'t get proper response')
            print(msgs['error'] + 'Response code: ' +
                  str(response.status_code))
            continue
        body = response.json()
        if 'error' in body:
            err_content = content['error']
            print_error_msg(msgs['error'], err_content['error_code'],
                            err_content['error_msg'])
            continue
        for friend in body['response']:
            info = [msgs['info'], (str(counter) + '.').rjust(6) + ' ',
                    friend['first_name'].ljust(24),
                    friend['last_name'].ljust(24),
                    '(id{})'.format(friend['id'])]
            line = ''.join(info)
            if len(line) > max_len:
                max_len = len(line)
            friends.append(line)
            counter += 1
    print('=' * max_len)
    print(msgs['info'] + 'User\'s friends are:')
    print('\n'.join(friends))
    print('=' * max_len)


def print_albums_info(msgs, albums_list):
    lines = []
    counter = 1
    for album in albums_list:
        lines.append('{}{}{}{}{}'.format(msgs['info'],
                                         (str(counter) + '.\t').rjust(4),
                                         'Size: {}'.format(album['size'])
                                         .ljust(12),
                                         ('id' + str(album['id'])).ljust(16),
                                         album['title']))
        counter += 1

    max_len = len(max(lines, key=len)) if len(lines) > 0 else 0
    print('=' * max_len)
    print(msgs['info'] + 'User\'s photo albums list:')
    print('\n'.join(lines))
    print('=' * max_len)


def divide_chunks(enumerable, n):
    for i in range(0, len(enumerable), n):
        yield enumerable[i:i + n]


if __name__ == '__main__':
    main()
