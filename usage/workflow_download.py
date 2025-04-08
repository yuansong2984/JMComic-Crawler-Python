from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
1122557
1122567
1123136
1123322
1123483
1123144
1123424
1123922
1121637
1124234
1122359
1110932
1114769
1115972
1116813
1116832
1117283
1117764
1117794
1117795
1118242
1118233
1118584
1119118
1118585
27050
1119649
1119839
1111561
1101741
1102470
1104033
1104096
1104495
1104509
1104586
1107418
1107431
1107439
1107528
1107545
1094608
486772
1094998
1095364
1095537
1095395
1095404
1096727
1097283
1097349
1098176
1098201
1092454
1090678
1083962
1077185
302808
244658
386001
403075
432840
540167
210427
100409
178432
1081635
1082486
1082843
1081548
1081532
1081161
1081152
1051148
1051156
1052240
1052888
1055333
1058685
1058413
1058053
1059526
1061491
1062394
1063179
1065075
1065217
1067683
1067693
1067702
1067722
1062501
1069046
1069049
1069045
1069030
1069033
1069042
1070815
1070897
1072654
1072661
1076943
1079346
1079515
1079671
1079681
1080417
1073120
1073333
1073194
1073797
1073808
1073995
1074261
1074743
315089
1075470
1075487
1075590
1078907
1078894
1079288
1079294
1058518
1058521
368816
1079392
1074221
1075896
1076950
1076955
1077803
1078297
1069312
1068594
1059742
1059761
1059753
1059571
600341
1016802
1024980
1037259
1045703
1046534
1049566
1050135
1050164
1050589
1049670
1049517
1049678
1049662
1049687
1049368
1048498
1048225
1045384
1047976
1047443
1047501
1047383
1047239
1046524
473469
274125
334128
314840
307440
243109
593090
603541
626220
630631
634783
637421
641342
641764
642744
644091
1013691
1024172
1029349
1046440
376409
378291
409200
1045440
1045677
1045615
1045684
1045688
1046149
1046167
1046185
1046204
1046231
1042559
1043941
1044652
1044653
1044708
1040860
1028992


'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
