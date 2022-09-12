import configparser

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('relay_node.ini')
    print(config.sections())
    for section in config.sections():
        for key in config[section]:
            print(section, key, config[section][key])