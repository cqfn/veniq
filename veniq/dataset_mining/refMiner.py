import os
import subprocess
from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, Optional, Union, Dict

from pebble import ProcessPool
from tqdm import tqdm

dir_to_analyze = [('rishabh115/Interview-Questions', 102), ('Snailclimb/JavaGuide', 4606),
                  ('MisterBooo/LeetCodeAnimation', 8288), ('lihengming/spring-boot-api-project-seed', 30851),
                  ('ouchuangxin/leave-sample', 51440), ('awsdocs/aws-lambda-developer-guide', 52103),
                  ('GoogleLLP/SuperMarket', 66100), ('JunzhouLiu/BILIBILI-HELPER', 69551),
                  ('arawn/building-modular-monoliths-using-spring', 81334), ('EiletXie/cloud2020', 86282),
                  ('spring-projects/spring-petclinic', 89351), ('zo0r/react-native-push-notification', 104678),
                  ('Snailclimb/guide-rpc-framework', 112343), ('medcl/elasticsearch-analysis-ik', 114714),
                  ('lenve/vhr', 144624), ('react-native-community/react-native-video', 175864),
                  ('intel-isl/OpenBot', 186423), ('nic-delhi/AarogyaSetu_Android', 202079),
                  ('ityouknow/spring-boot-examples', 229057), ('fuzhengwei/itstack-demo-design', 244164),
                  ('trojan-gfw/igniter', 250506), ('newbee-ltd/newbee-mall', 266433), ('alibaba/taokeeper', 305252),
                  ('kekingcn/kkFileView', 313775), ('qq53182347/liugh-parent', 379931), ('Tencent/APIJSON', 393850),
                  ('alibaba/COLA', 396781), ('firebase/quickstart-android', 435428),
                  ('cats-oss/android-gpuimage', 465871), ('xuxueli/xxl-job', 470849), ('TheAlgorithms/Java', 506454),
                  ('react-native-community/react-native-camera', 512604), ('google/grafika', 553156),
                  ('termux/termux-app', 611291), ('DuGuQiuBai/Java', 652678),
                  ('android/user-interface-samples', 665209), ('kdn251/interviews', 674404),
                  ('xkcoding/spring-boot-demo', 675198), ('airbnb/lottie-android', 682626),
                  ('Red5/red5-server', 715723), ('feast-dev/feast', 744875), ('elunez/eladmin', 745583),
                  ('zhisheng17/flink-learning', 753262), ('careercup/CtCI-6th-Edition', 770012),
                  ('jitsi/jitsi-videobridge', 806428), ('Notsfsssf/Pix-EzViewer', 875003),
                  ('wix/react-native-navigation', 897164), ('yuliskov/SmartTubeNext', 911945),
                  ('google/exposure-notifications-android', 929237), ('alibaba/easyexcel', 1041929),
                  ('bigbluebutton/bigbluebutton', 1085022), ('mission-peace/interview', 1111425),
                  ('square/retrofit', 1199658), ('alibaba/spring-cloud-alibaba', 1266374),
                  ('MalitsPlus/ShizuruNotes', 1275918), ('zhangdaiscott/jeecg-boot', 1292101),
                  ('cabaletta/baritone', 1308293), ('williamfiset/Algorithms', 1316427),
                  ('PhilJay/MPAndroidChart', 1317015), ('dromara/soul', 1333632), ('halo-dev/halo', 1341126),
                  ('CarGuo/GSYVideoPlayer', 1423273), ('zuihou/zuihou-admin-cloud', 1424116),
                  ('FabricMC/fabric', 1491033), ('arduino/Arduino', 1524590), ('paascloud/paascloud-master', 1551821),
                  ('square/okhttp', 1793311), ('metersphere/metersphere', 1878372), ('YunaiV/SpringBoot-Labs', 1920961),
                  ('intuit/karate', 1943008), ('didi/kafka-manager', 1964652), ('YunaiV/onemall', 2001309),
                  ('alibaba/arthas', 2025697), ('GeyserMC/Geyser', 2026042), ('seven332/EhViewer', 2038173),
                  ('dromara/hmily', 2056099), ('Netflix/eureka', 2089056), ('hyb1996/Auto.js', 2093478),
                  ('TeamNewPipe/NewPipe', 2096544), ('eclipse/paho.mqtt.java', 2310603),
                  ('Blankj/AndroidUtilCode', 2336083), ('alibaba/DataX', 2337300),
                  ('GoogleCloudPlatform/DataflowTemplates', 2390881), ('zxing/zxing', 2394547),
                  ('skylot/jadx', 2398208), ('gedoor/MyBookshelf', 2433150), ('ctripcorp/apollo', 2484217),
                  ('open-telemetry/opentelemetry-java', 2497056), ('elastic/elasticsearch-hadoop', 2685341),
                  ('macrozheng/mall', 2734011), ('macrozheng/mall-swarm', 2743678), ('antlr/antlr4', 2942372),
                  ('bjmashibing/InternetArchitect', 3023831), ('mockito/mockito', 3100208),
                  ('Anuken/Mindustry', 3165740), ('Tencent/QMUI_Android', 3283264),
                  ('iluwatar/java-design-patterns', 3372026), ('spring-projects/spring-data-examples', 3434461),
                  ('alibaba/Sentinel', 3515353), ('MinecraftForge/MinecraftForge', 3561793),
                  ('macrozheng/mall-learning', 3634489), ('nextcloud/android', 3900547),
                  ('CloudburstMC/Nukkit', 3915530), ('linlinjava/litemall', 3935420), ('alibaba/canal', 4096817),
                  ('awslabs/djl', 4104489), ('apache/incubator-dolphinscheduler', 4344024),
                  ('material-components/material-components-android', 4404295), ('seata/seata', 4609792),
                  ('alibaba/Alink', 4875343), ('alibaba/nacos', 5292544), ('apache/zookeeper', 6622995),
                  ('eclipse/eclipse.jdt.ls', 6635079), ('thingsboard/thingsboard', 6659511),
                  ('alibaba/fastjson', 7307675), ('apache/jmeter', 8936436), ('eclipse/che', 8942195),
                  ('grpc/grpc-java', 9624796), ('apache/shardingsphere', 9863162), ('javaparser/javaparser', 10166521),
                  ('apache/dubbo', 10205555), ('apache/skywalking', 10503947), ('google/ExoPlayer', 11255771),
                  ('runelite/runelite', 12005738), ('eclipse/milo', 12661330), ('Graylog2/graylog2-server', 12889377),
                  ('linkedin/dagli', 13466753), ('eclipse/eclipse-collections', 14274298),
                  ('checkstyle/checkstyle', 14632745), ('oracle/helidon', 14730527), ('eclipse/elk', 15312689),
                  ('netty/netty', 16991168), ('quarkusio/quarkus', 18719448), ('eugenp/tutorials', 19116189),
                  ('jitsi/jitsi', 19250523), ('spring-projects/spring-boot', 19700970), ('alibaba/druid', 19762494),
                  ('dbeaver/dbeaver', 20613997), ('eclipse/jetty.project', 21207188), ('apache/pulsar', 22404445),
                  ('google/guava', 26607422), ('ballerina-platform/ballerina-lang', 27349222),
                  ('OpenAPITools/openapi-generator', 28150393), ('SonarSource/sonarqube', 30102895),
                  ('eclipse/openj9', 31436930), ('openhab/openhab-addons', 36772862),
                  ('eclipse/deeplearning4j', 37688626), ('spring-projects/spring-framework', 42944872),
                  ('prestodb/presto', 43730138), ('bazelbuild/bazel', 44548383), ('androidx/androidx', 46353691),
                  ('oracle/graal', 63148282), ('apache/flink', 64700358), ('NationalSecurityAgency/ghidra', 67423006),
                  ('apache/hadoop', 94700218), ('elastic/elasticsearch', 112288504), ('apache/netbeans', 297452969),
                  ('Azure/azure-sdk-for-java', 471640138)]

new_dataset = set()
folder_to_analyze = r'/hdd/new_dataset/RefactoringMiner/RefactoringMiner/build/distributions/RefactoringMiner-2.0.1/bin/01'


# for folder in Path(folder_to_analyze).iterdir():
#     if folder.is_dir():
#         # print(folder)
#         for subfolder in folder.iterdir():
#             if subfolder.is_dir():
#                 dir = subfolder.parts[-2] + '/' + subfolder.parts[-1]
#                 #dir = subfolder.parts[-1]
#                 new_dataset.add(dir)


#
# old_dataset = set()
# print('##############################################')
# for folder in Path('/dataset/01').iterdir():
#     if folder.is_dir():
#         # print(folder)
#         for subfolder in folder.iterdir():
#             if subfolder.is_dir():
#                 dir = subfolder.parts[-2] + '/' + subfolder.parts[-1]
#                 old_dataset.add(dir)
#                 # print(dir)
#
# miss = old_dataset.difference(new_dataset)
# os.chdir(Path('/hdd/new_dataset/02'))
# for dir in miss:
#     repo_url = f'https://github.com/{dir}.git'
#     print(repo_url)
#     subprocess.Popen(['git', 'clone', repo_url])
#     # print(miss)

def get_commits_number(t: Tuple[str, int]) -> Dict[str, Union[str, int]]:
    p = Path(folder_to_analyze, t[0])
    os.chdir(p)
    command = ['git', 'rev-list', '--all', '--count']
    # print(command)
    output = subprocess.check_output(command)
    return {
        'folder': t[0],
        'java_files': t[1],
        'commits_number': int(output.strip())
    }


def run_ref_miner(folder: str):
    p = Path(folder)
    f_err = open(f"{'_'.join(p.parts)}.err.txt")
    f_out = open(f"{'_'.join(p.parts)}.out.txt")
    command = ['./RefactoringMiner', '-a', f"01/{folder}"]
    print(command)
    subprocess.Popen(command, stderr=f_err, stdout=f_out).wait()


system_cores_qty = 3
# dir_to_analyze = {}
# for x in new_dataset:
#     java_files = [x.stat().st_size for x in Path(folder_to_analyze, x).glob('**/*.java')]
#     sum_size = sum(java_files)
#     dir_to_analyze[x] = sum_size

# dir_to_analyze = OrderedDict(sorted(dir_to_analyze.items(), key=lambda x: x[1]))

# dir_to_analyze = [x[0] for x in dir_to_analyze]
# dir_to_analyze = [dir_to_analyze[0]]
import pandas as pd

with ProcessPool(system_cores_qty) as executor:
    future = executor.map(get_commits_number, dir_to_analyze)
    result = future.result()
    df = pd.DataFrame(columns=['folder', 'java_files', 'commits_number'])
    for filename in tqdm(dir_to_analyze):
        res = next(result)
        print(res)
        df = df.append(res, ignore_index=True)
    df.to_csv('commits.csv')
