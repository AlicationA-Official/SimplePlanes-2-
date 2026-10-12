"""Compose Chinese entries for the untranslated designer parts.

English descriptions are taken verbatim from data/parts_to_translate.json, so the
generated keys are guaranteed to match the game's exact strings.
"""
import json
import os

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(WS, 'data', 'parts_to_translate.json')
OUT = os.path.join(WS, 'patch', 'gap_fill_parts.json')

# name -> (chinese name, chinese description)
T = {
    # ---- Wheels / landing gear (0.7.7-0.7.8 新增) ----
    'A-Frame': ('A 型架起落架', '粗犷的 A 型架越野支柱，配肥厚的气球胎。专为简陋场地和偏远简易跑道而生。'),
    'A-Frame Bare': ('A 型架起落架（裸架）', '把 A 型架越野支柱剥到只剩框架。同样的野外脾气，稍微轻一点。'),
    'Aero': ('气动整流起落架', '带整流轮罩的流线型轻型飞机支柱。阻力低，适合慢速运动型飞机。'),
    'Airliner Front': ('客机前起落架', '为客机和大型喷气机准备的高大双轮前起落架。'),
    'Airliner Rear': ('客机主起落架', '搭乘三轮转向架的重型客机主起落架。为大块头准备。'),
    'Beefcake': ('壮硕起落架', '粗壮的主支柱，长行程悬挂加肥厚轮胎。硬着陆全靠肌肉硬扛。'),
    'Braced': ('支撑式前起落架', '带弹射杆的支撑式 V 型架前起落架。'),
    'Forged': ('锻造起落架', '采用实心支柱的前起落架。'),
    'GA Bent': ('通航弯管起落架', '小巧而有弹性的悬臂支柱。'),
    'Gear Bay': ('起落架舱', '在机身上开出一个轮舱，并配上随起落架开合的舱门。让可收放起落架有个收纳之处。'),
    'Heavy': ('重型起落架', '装在四轮转向架上的重型主支柱。为搬运真正的大重量而生。'),
    'Hollow': ('空心起落架', '采用空心支柱、略微更轻的前起落架。'),
    'Ivan': ('伊万式起落架', '粗犷的 V 型架前起落架，配长活塞支柱，造型源自重型东方阵营喷气机。'),
    'Lever': ('杠杆式起落架', '杠杆式主支柱，悬挂行程长，着陆柔和有弹性。'),
    'Stout': ('矮壮起落架', '装在四轮转向架上的短粗主支柱。矮而结实，专负重载。'),
    'Trailing Link': ('拖曳臂起落架', '拖曳臂式主支柱，连杆能吸收颠簸，着陆更平稳。'),
    'Tripod': ('三脚架起落架', '三脚架支撑的主支柱，配剪式支柱。稳定可靠，战斗机风格。'),
    'Wheel Assembly': ('轮组总成', '多轮机轮总成。先选择轮位布局样式（单轮、双轮、四轮……），再选一套应用到总成中每个轮子的轮胎与轮辋。可直接固定在机身上，也可装到起落架支柱上。'),
    'Wing': ('翼载起落架', '紧凑的翼下主起落架，收起后很薄，特别适合塞进细薄的机翼下方。'),
    'Legacy Resizable Wheel': ('旧版可调机轮', '可以任意改形、改尺寸的机轮。还能在零件属性面板里把它连接到汽车发动机上获取动力。'),

    # ---- Engines / propulsion ----
    'Exhaust': ('排气管', '一根排气管。装到任意发动机上，它就会排出该发动机燃烧的废气。多放几根可以拼出排气歧管或集气环——发动机会把废气分配给所有排气管，所以八根管子每根只分到八分之一。'),
    'Gearbox Large': ('大型变速箱', '在动力系统中传递旋转动力。可通过齿比在扭矩与转速之间做权衡，并据此调校性能。'),
    'Gearbox Long': ('长型变速箱', '在动力系统中传递旋转动力。可通过齿比在扭矩与转速之间做权衡，并据此调校性能。'),
    'Gearbox Offset': ('偏置变速箱', '在动力系统中传递旋转动力。可通过齿比在扭矩与转速之间做权衡，并据此调校性能。'),
    'Legacy Car Engine': ('旧版汽车发动机', '可调机轮可以连接到这台发动机上获取动力。选中机轮并打开零件属性面板，即可把机轮连接到发动机。机轮需要离发动机足够近。'),
    'Large Turboprop': ('大型涡桨发动机', '我们造过的、还能带动螺旋桨的最大燃气轮机。轴功率大到必须用对转螺旋桨，也大到需要你全神贯注。'),
    'Medium Turboprop': ('中型涡桨发动机', '勤恳耐用的燃气轮机，转速恒定，全凭螺旋桨说话。往大机翼上栓四台，就能去拉货了。'),
    'Small Turboprop': ('小型涡桨发动机', '紧凑的燃气轮机，通过减速变速箱驱动动力系统。'),
    'VTOL Inlet': ('VTOL 进气口', '大型进气口，能为任何喷气发动机吸入足够空气。放在机头附近、气流更平稳的位置效果更好。'),
    'VTOL Slim Inlet': ('VTOL 细型进气口', '进气口负责吸入空气，让喷气发动机能顺畅呼吸。大多数发动机至少需要两个这种细型进气口。'),

    # ---- Structure ----
    'Curved Fuselage': ('弧形机身', '程序化弧形机身段。可自定义其形状、尺寸与厚度。'),
    'Hole': ('开孔', '在机身类零件上挖出可自定义的开口，用来做货舱、弹舱、轮舱等等。只对机身类零件有效。'),
    'Hemisphere': ('半球体', '有时你不需要一整个球。有时你只需要半个球。'),
    'Sphere': ('球体', '球是所有玩具里最棒的那一个。'),
    'Structural Panel': ('结构板', '看起来像机翼，但没有机翼的物理模拟。适合给那些以前为了美观堆了很多机翼的设计使用。换成它之后，这些设计会跑得更快一些，因为它没有机翼物理开销。'),
    'Window': ('窗户', '在任意机身类零件上安装可自定义的窗户。只对机身类零件有效。'),
    'Legacy Floating Block': ('旧版浮筒方块', '这些方块会浮起来！有策略地摆在飞机周围可以当浮筒，摆到船体某些位置就能做出水上飞机。要让它们发挥作用得算点数值，所以别用太多。'),
    'Legacy Fuselage Block': ('旧版机身方块', '一块顶所有。借助零件属性窗口，这个方块可以有很多种缩放方式：边缘可以改形状、可以装燃料，还自带浮力。上手需要一点时间，但绝对值得。'),
    'Legacy Fuselage Cone': ('旧版机身鼻锥', '与机身方块配套的专用鼻锥。'),
    'Legacy Glass Fuselage': ('旧版玻璃机身', '就像机身，不过是玻璃的！想要最好的玻璃效果，请指定一个光滑度 90% 到 100% 的材质，然后把不透明度设为 0%。分隔面会自动隐藏，而且默认开启平滑。'),
    'Legacy Hollow Fuselage': ('旧版空心机身', '外形看起来是空心的专用机身方块，其实相当结实。'),
    'Legacy Hollow Glass Fuselage': ('旧版空心玻璃机身', '就像空心机身，不过是玻璃的！想要最好的玻璃效果，请指定一个光滑度 90% 到 100% 的材质，然后把不透明度设为 0%。分隔面会自动隐藏，而且默认开启平滑。'),
    'Legacy Angled Corner': ('旧版斜角转角块', '这是一块转角件。拼图时总要先找转角件。这条建议在造飞机时其实并不适用，但它依然是条好建议。'),
    'Legacy Curved Block': ('旧版弧形方块', '基本和斜角方块一样，只不过是弧形的。区别纯粹是外观，而这很重要，因为你造的是最漂亮的飞机。'),
    'Legacy Curved Corner': ('旧版弧形转角块', '斜角转角件的弧形版本而已。'),
    'Legacy Curved Reducer Block': ('旧版弧形过渡方块', '和过渡方块一样，只是变成弧形的了。'),
    'Legacy Long Angled Block': ('旧版长斜角方块', '就是一块长长的斜角方块。'),
    'Legacy Reducer Block': ('旧版过渡方块', '就是一块从 2 变 1 的方块。如果你是乐观派，也可以说它从 1 变成 2——一个扩张件。'),
    'Legacy Riser Block': ('旧版增高方块', '有时候你希望某块方块比旁边的方块高一点。'),
    'Legacy Nose Cone': ('旧版鼻锥', '鼻锥不仅好看，而且设计上阻力极低。尺寸可以通过菜单调整。'),

    # ---- Wings ----
    'Legacy Horizontal Stabilizer': ('旧版水平安定面', '带升降舵的翼段。能为飞机提供抬头和低头的控制。'),
    'Legacy Primary Wing': ('旧版主翼', '已经配好副翼和部分燃料的翼段。主翼用于为飞机提供主要升力，并提供左右滚转的控制。'),
    'Legacy Structural Wing': ('旧版结构翼', '比普通机翼更结实，也确实能提供升力，但不能安装控制面。而且它更重。'),
    'Legacy Vertical Stabilizer': ('旧版垂直安定面', '带方向舵的翼段。垂直安定面能防止飞机不受控地向左或向右偏航。'),

    # ---- Interiors ----
    'Legacy Cockpit': ('旧版座舱', '每架飞机至少都需要一个。别担心，它是坚不可摧的，所以你的飞行员永远安全。'),
    'Legacy Cockpit Block': ('旧版座舱方块', '模块化座舱件，适合其他座舱都不合用的时候。'),
    'Legacy Cockpit Corner': ('旧版座舱转角块', '座舱方块的转角件。'),
    'Legacy Cockpit Angled Corner': ('旧版座舱斜角转角块', '座舱方块的斜角转角件。'),
    'Legacy Historic Cockpit': ('旧版复古座舱', '给追求历史感的建造者准备的座舱。'),
    'Legacy Sleek Cockpit': ('旧版流线座舱', '就是一款稍微流线一点的座舱。'),

    # ---- Weapons ----
    'Legacy Rocket': ('旧版火箭', '一枚 2.75 英寸火箭弹，只要飞行员有技术，对付地面目标非常有效。'),
}


def main():
    parts = json.load(open(SRC, encoding='utf-8'))
    out, missing = {}, []
    for p in parts:
        name, desc = p['name'], p['description']
        if name not in T:
            missing.append(name)
            continue
        cn_name, cn_desc = T[name]
        out[name] = cn_name
        if desc:
            out[name + '\n' + desc] = cn_name + '\n' + cn_desc
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('parts in source      : %d' % len(parts))
    print('translated parts     : %d' % len(T))
    print('generated entries    : %d' % len(out))
    if missing:
        print('!! still missing     : %s' % missing)
    print('written              : %s' % OUT)


if __name__ == '__main__':
    main()
