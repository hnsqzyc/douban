import scrapy.cmdline


def main():
    # scrapy.cmdline.execute(argv=['scrapy', 'crawl', 'dban', '-a', 'params='+'{"remote_resource": true}'])

    scrapy.cmdline.execute(argv=['scrapy', 'crawl', 'dban_get_photo', '-a', 'params='+'{"remote_resource": true}'])


if __name__ == '__main__':
    main()