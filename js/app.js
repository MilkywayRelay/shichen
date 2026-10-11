/* ══════════════════════════════════════════════════════════════
   识尘 · SHICHEN PROJECT  主脚本
   浮尘粒子 / 加载序列 / 认知稳定度 / 档案交互
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ══════════════════════════════════════════
     一、浮尘粒子系统
     ══════════════════════════════════════════ */
  var Dust = (function () {
    var cv = $('#dust-canvas');
    if (!cv) return { setStorm: function () {} };
    var ctx = cv.getContext('2d');
    var W = 0, H = 0, DPR = 1;
    var parts = [];
    var mouse = { x: -9999, y: -9999, active: false };
    var storm = 0, stormTarget = 0;
    var streaks = [];
    var t = 0;

    function resize() {
      DPR = Math.min(window.devicePixelRatio || 1, 2);
      W = cv.clientWidth; H = cv.clientHeight;
      cv.width = W * DPR; cv.height = H * DPR;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      build();
    }

    function build() {
      var target = Math.round(Math.min(190, Math.max(48, (W * H) / 16000)));
      parts = [];
      for (var i = 0; i < target; i++) parts.push(spawn(true));
    }

    function spawn(anywhere) {
      var p = {
        x: Math.random() * W,
        y: anywhere ? Math.random() * H : H + 12,
        vx: (Math.random() - 0.5) * 0.22,
        vy: -(0.08 + Math.random() * 0.3),
        r: 0.5 + Math.random() * 1.5,
        a: 0.12 + Math.random() * 0.42,
        ph: Math.random() * Math.PI * 2,
        sp: 0.4 + Math.random() * 1.2
      };
      return p;
    }

    function draw() {
      t += 0.006;
      storm += (stormTarget - storm) * 0.045;

      ctx.clearRect(0, 0, W, H);

      // — 尘暴：能量乱流 —
      if (storm > 0.02) {
        ctx.save();
        ctx.globalCompositeOperation = 'multiply';
        for (var s = 0; s < 3; s++) {
          var p0 = (t * (1.4 + s * 0.5) + s * 7) % 1;
          ctx.beginPath();
          ctx.strokeStyle = s === 1
            ? 'rgba(94,78,124,' + (0.16 * storm) + ')'
            : 'rgba(158,58,44,' + (0.14 * storm) + ')';
          ctx.lineWidth = 0.8 + s * 0.5;
          ctx.moveTo(-20, H * p0);
          ctx.bezierCurveTo(W * 0.3, H * p0 - 60 * Math.sin(t * 3 + s),
                            W * 0.7, H * p0 + 60 * Math.cos(t * 2.4 + s),
                            W + 20, H * p0 - 20);
          ctx.stroke();
        }
        ctx.restore();
      }

      // — 粒子 —
      ctx.save();
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];

        // 湍流
        if (storm > 0.02) {
          p.vx += Math.sin(p.y * 0.011 + t * 5) * 0.09 * storm;
          p.vy += Math.cos(p.x * 0.009 + t * 4) * 0.05 * storm;
        } else {
          p.vx += Math.sin(t * p.sp + p.ph) * 0.0055;
        }

        // 鼠标排斥
        var dxm = p.x - mouse.x, dym = p.y - mouse.y;
        var dm2 = dxm * dxm + dym * dym;
        if (dm2 < 20000 && dm2 > 0.01) {
          var f = (1 - dm2 / 20000) * 0.55;
          var dm = Math.sqrt(dm2);
          p.vx += (dxm / dm) * f;
          p.vy += (dym / dm) * f;
        }

        p.x += p.vx; p.y += p.vy;
        p.vx *= 0.975; p.vy *= 0.975;
        p.vy -= storm > 0.02 ? 0 : 0.0055;           // 无风时缓缓上浮

        if (p.y < -14) { p.x = Math.random() * W; p.y = H + 10; p.vx = (Math.random() - 0.5) * 0.22; p.vy = -(0.08 + Math.random() * 0.3); }
        if (p.x < -14) p.x = W + 10;
        if (p.x > W + 14) p.x = -10;

        var twist = storm * 0.012 * Math.sin(p.y * 0.02 + t * 3);
        var alpha = p.a * (1 - storm * 0.35);

        ctx.beginPath();
        ctx.fillStyle = storm > 0.3
          ? 'rgba(140,90,72,' + alpha + ')'
          : 'rgba(105,100,90,' + alpha + ')';
        ctx.arc(p.x + twist * 40, p.y, p.r, 0, 6.2832);
        ctx.fill();
      }
      ctx.restore();

      // — 尘纱：邻近粒子连线 —
      ctx.save();
      ctx.lineWidth = 0.55;
      var maxD = 132;
      for (var a = 0; a < parts.length; a++) {
        for (var b = a + 1; b < parts.length; b++) {
          var pa = parts[a], pb = parts[b];
          var ddx = pa.x - pb.x; if (ddx > maxD || ddx < -maxD) continue;
          var ddy = pa.y - pb.y; if (ddy > maxD || ddy < -maxD) continue;
          var d = Math.sqrt(ddx * ddx + ddy * ddy);
          if (d < maxD) {
            var o = (1 - d / maxD) * 0.1 * (1 + storm * 1.6);
            ctx.strokeStyle = storm > 0.3
              ? 'rgba(120,80,110,' + o + ')'
              : 'rgba(120,112,96,' + o + ')';
            ctx.beginPath();
            ctx.moveTo(pa.x, pa.y);
            ctx.lineTo(pb.x, pb.y);
            ctx.stroke();
          }
        }
      }
      // — 与光标的牵引线 —
      if (mouse.active) {
        for (var k = 0; k < parts.length; k++) {
          var pk = parts[k];
          var mx = pk.x - mouse.x, my = pk.y - mouse.y;
          var md = Math.sqrt(mx * mx + my * my);
          if (md < 170) {
            ctx.strokeStyle = 'rgba(176,141,79,' + ((1 - md / 170) * 0.26) + ')';
            ctx.beginPath();
            ctx.moveTo(pk.x, pk.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }
      ctx.restore();

      // — 尘暴火花 —
      if (storm > 0.35 && Math.random() < 0.1 * storm) {
        streaks.push({
          y: Math.random() * H,
          life: 1,
          w: 40 + Math.random() * 160,
          c: Math.random() < 0.5 ? '158,58,44' : '176,141,79'
        });
      }
      ctx.save();
      for (var q = streaks.length - 1; q >= 0; q--) {
        var st = streaks[q];
        st.life -= 0.045;
        if (st.life <= 0) { streaks.splice(q, 1); continue; }
        ctx.fillStyle = 'rgba(' + st.c + ',' + (st.life * 0.3) + ')';
        ctx.fillRect(0, st.y, W, st.w * (1 - st.life) * 0.06 + 0.6);
      }
      ctx.restore();

      requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('mousemove', function (e) {
      mouse.x = e.clientX; mouse.y = e.clientY; mouse.active = true;
    }, { passive: true });
    window.addEventListener('mouseout', function () { mouse.active = false; mouse.x = mouse.y = -9999; });
    window.addEventListener('touchmove', function (e) {
      var tt = e.touches[0];
      if (tt) { mouse.x = tt.clientX; mouse.y = tt.clientY; mouse.active = true; }
    }, { passive: true });

    resize();
    if (!reduce) requestAnimationFrame(draw);
    else { ctx.clearRect(0, 0, W, H); }

    return {
      setStorm: function (on) { stormTarget = on ? 1 : 0; }
    };
  })();

  /* ══════════════════════════════════════════
     二、自定准星
     ══════════════════════════════════════════ */
  (function reticle() {
    if (reduce || window.matchMedia('(max-width:860px)').matches) return;
    var r = $('.reticle'), c = $('.reticle-coord');
    if (!r) return;
    var tx = innerWidth / 2, ty = innerHeight / 2, x = tx, y = ty, on = false;
    document.body.classList.add('custom-cursor');

    window.addEventListener('mousemove', function (e) {
      tx = e.clientX; ty = e.clientY;
      if (!on) { on = true; r.classList.add('is-active'); c.classList.add('is-active'); }
      c.style.transform = 'translate(' + tx + 'px,' + ty + 'px)';
      var cx = $('#coord-x'), cy = $('#coord-y');
      if (cx) cx.textContent = String(Math.round(tx)).padStart(4, '0');
      if (cy) cy.textContent = String(Math.round(ty)).padStart(4, '0');
    }, { passive: true });

    (function loop() {
      x += (tx - x) * 0.22; y += (ty - y) * 0.22;
      r.style.transform = 'translate(' + x + 'px,' + y + 'px)';
      requestAnimationFrame(loop);
    })();

    document.addEventListener('mouseover', function (e) {
      if (e.target.closest('a,button,.trow__head,.wcard,.fcard,.story,.archive__dots i')) r.classList.add('is-hover');
    });
    document.addEventListener('mouseout', function (e) {
      if (e.target.closest('a,button,.trow__head,.wcard,.fcard,.story,.archive__dots i')) r.classList.remove('is-hover');
    });
  })();

  /* ══════════════════════════════════════════
     三、数据
     ══════════════════════════════════════════ */

  var TICKER = [
    '尘暴预警 · 北纬 41° 海域检测到油膜状异常散射反光',
    '尘晶矿脉解析进度 3,412 / 4,000',
    '联合政府通讯部 · 本季度认知污染清洗 1,204 例',
    '密斯卡托尼克大学 · 秋季学期录取通过率 6.2%',
    'WARN · 地下教会活动半径持续扩张，请勿直视',
    '调查社总部 · 第 524 号堡垒完成新一轮迭代',
    '后尘样本 · 矿区提前 47 分钟记录到崩塌声',
    '类型学代号体系 · 试炼通过率 11.7%',
    '旧日投影 · 已确认 19 处，其中 3 处无法解析'
  ];

  var TECHS = [
    {
      n: 'I', cn: '监视与预测', en: 'OBSERVATIO ET PRAEDICTIO',
      brief: '对尘有关事物的绝缘与抽离',
      body: '观察或测量若干意识信息在若干时空点所呈现的状态，推演得出尘纱整体的性质及其运动规律。非常类似打开黑箱的过程——根据观察结果推理估计尘域的尘寰核心，借助计算机估算尘纱内尘的运动方式（类似回归分析）。',
      tags: ['尘的综合监测系统', '黑箱建模', '尘寰核心定位']
    },
    {
      n: 'II', cn: '控制', en: 'CONTINENTIA',
      brief: '尘封、采录与收容',
      body: '根据监视与预测所得的尘纱性质与运动规律，把尘相关事物投射到特定载体并令之固化。注意投射与投影不同：投射可以截取片段，投影力求整体的还原。',
      tags: ['人体尘存储器', '以人为载体的收容', '尘封协议']
    },
    {
      n: 'III', cn: '扭曲 · 变形', en: 'DISTORSIO',
      brief: '对尘有关事物的压缩与展开',
      body: '通过改变尘寰核心收缩尘寰，以及展开收拢的尘寰、释放尘像体、令其投影到特定设备。这个过程与「改写」不同，不会扭曲尘寰的形态。',
      tags: ['召唤旧日', '尘寰核心', '专属尘寰构建']
    },
    {
      n: 'IV', cn: '改写', en: 'TRANSCRIPTIO',
      brief: '对尘有关事物的解析与转译',
      body: '把信息拆析为若干以关键点为核心的小型子信息，对每一子信息以不同方式进行扭曲，从而改写整体信息本身。按信息的维度拆分后扭曲子信息——如将听觉信息改成波的图像后再解析为向量、把向量变为音频输出——从而避免直接接收来自旧日的信息，降低信息污染的风险。',
      tags: ['调查社通讯器原理', '精神分析 · 催眠', '针对旧日的心理治疗']
    },
    {
      n: 'V', cn: '尘间相互作用', en: 'INTERACTIO',
      brief: '利用尘的相互作用毁灭或约束部分尘',
      body: '尘存在正负之分，根源相同的尘属于同极，反之则属于异极。同极的尘相容共生，异极的尘相斥毁灭。可利用尘的相斥或相容性约束或消减尘。',
      tags: ['维度炸弹', '防护屏障', '个体持有的特殊武器']
    }
  ];

  var FAC_GLYPHS = {
    shield: '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M24 4 42 12v14c0 10-8 16-18 18-10-2-18-8-18-18V12z"/><path d="M24 16v16M16 24h16"/></svg>',
    globe: '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="24" cy="24" r="18"/><ellipse cx="24" cy="24" rx="8" ry="18"/><path d="M6 24h36M9 14h30M9 34h30"/></svg>',
    flask: '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M18 6h12v12l10 20a5 5 0 0 1-4.5 7h-23A5 5 0 0 1 8 38l10-20z"/><path d="M13 30h22"/></svg>',
    book:  '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M24 12c-4-3-10-4-16-4v30c6 0 12 1 16 4 4-3 10-4 16-4V8c-6 0-12 1-16 4z"/><path d="M24 12v30"/></svg>',
    mask:  '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M6 14c0 14 6 24 18 28 12-4 18-14 18-28-6 3-12 4-18 4S12 17 6 14z"/><circle cx="17" cy="24" r="2.4" fill="currentColor" stroke="none"/><circle cx="31" cy="24" r="2.4" fill="currentColor" stroke="none"/></svg>',
    eye:   '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M4 24s8-12 20-12 20 12 20 12-8 12-20 12S4 24 4 24z"/><circle cx="24" cy="24" r="6"/></svg>',
    tent:  '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M24 6c-5 0-8 4-8 9s3 8 3 12-3 8-8 8-8-3-8-8"/><path d="M24 6c5 0 8 4 8 9s-3 8-3 12 3 8 8 8 8-3 8-8"/><circle cx="24" cy="12" r="3.2" fill="currentColor" stroke="none"/></svg>',
    compass:'<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="24" cy="24" r="18"/><path d="M32 16 20 20l-4 12 12-4z"/></svg>'
  };

  var FACTIONS = [
    {
      g: 'shield', cn: '新约调查社', en: 'SOCIETAS INVESTIGATIONIS NOVA',
      p: '先于国家存在，是对抗旧日的核心机构。有总部与分部之分——总部是一艘坐落公海的庞大舰船；分部遍布世界各地（原则之一：一个设备齐全的调查员即可成为一个分部）。',
      f1: '社会关系', v1: '与所有机构保持松散联系',
      f2: '位置', v2: '社会网络的结构洞',
      f3: '在册', v3: 'ENFP / ENTJ / ISFJ / ISTP'
    },
    {
      g: 'globe', cn: '联合政府', en: 'GOVERNMENTUM UNITUM',
      p: '专为处理旧日而生的政治机构。国家联盟，各国家政府提供资金、人力与军队。不但需要杀死旧日，还需处理旧日带来的经济与后续影响。',
      f1: '下属', v1: '通讯 / 行动 / 行政 / 法律',
      f2: '要员', v2: 'ESTJ · ESFJ · INFJ',
      f3: '备注', v3: '地下市场臭名昭著'
    },
    {
      g: 'flask', cn: '研究所', en: 'INSTITUTUM',
      p: '附属于联合政府，但有时会脱离政府追求自己的目的。技术似乎很高，但似乎被什么控制着。组织内个体的目标完全不同。',
      f1: '性质', v1: '相互利用的塑料友谊团',
      f2: '要员', v2: 'ENFJ · INTP',
      f3: '口号', v3: '惟更善之善'
    },
    {
      g: 'book', cn: '密斯卡托尼克大学', en: 'UNIVERSITAS MISKATONICA',
      p: '传授旧日相关知识的教育机构中最有名的一座。大量调查员及联合政府官员都毕业自该大学。师生各自主攻自己的领域，但会遵循学术规范与学术伦理。',
      f1: '政治权力', v1: '与官方等同',
      f2: '技术', v2: '很高，实战弱于调查社',
      f3: '要员', v3: 'ISFP · 自由艺术家'
    },
    {
      g: 'mask', cn: '怪盗团', en: 'GREX FURUM',
      p: '活跃于尘寰的团队，略神出鬼没。活跃于地下市场，借识数交易换取自己需要的物资。似乎是希望改变现有的不合理制度。',
      f1: '社会关系', v1: '与政府等正式机构关系紧张',
      f2: '要员', v2: 'ISTJ · ESTP',
      f3: '符号', v3: '现场留下的镀金羽毛'
    },
    {
      g: 'eye', cn: '地下教会', en: 'ECCLESIA ABSCONDITA', hostile: true,
      p: '坐落于尘寰之间的非法宗教组织。官方似乎不太了解该机构。似乎知晓很多禁忌知识，似乎想用尘达到什么目的。',
      f1: '政治权力', v1: '罪犯',
      f2: '要员', v2: 'INTJ · ENTP',
      f3: '状态', v3: '目的不明 · 高度危险'
    },
    {
      g: 'tent', cn: '冒险小队', en: 'MANIPULUS',
      p: '拜ISTP调查员的身份所赐，与调查社关系非常密切。会接收奇怪（很多与尘相关）的委托，主要资金来自佣金——类似万事屋。',
      f1: '组织性', v1: '亲友组成，极高',
      f2: '要员', v2: 'ISTP · INFP · ESFP',
      f3: '目标', v3: '似乎希望岁月静好'
    },
    {
      g: 'compass', cn: '逐尘使 · 代行者', en: 'SECTATORES PULVIS', hostile: true,
      p: '并非登记在案的机构，而是自然产生的一类存在。代行者是被尘深度侵染或改造的自然生物 / 物体；逐尘使则追逐、利用尘，其活动会加剧尘的不稳定。',
      f1: '行为特征', v1: '常具攻击性',
      f2: '活动区域', v2: '尘晶矿区 · 古遗迹 · 尘寰附近',
      f3: '后果', v3: '诱发尘暴 · 改造环境'
    }
  ];

  var CHARS = [
    {
      code: 'ISFJ', role: '档案员', img: 'assets/char/isfj.webp?v=6',
      meta: { '性别': '女', '外观年龄': '约 23 岁', '身高': '163 cm', '所属': '新约调查社 · 档案部', '虹膜': '极浅婴儿蓝', '显性标记': '左眼下淡褐色泪痣' },
      quote: '她不愤怒，甚至不带情绪，只像整理过期文献一样自然。',
      note: '表层温和细致、不引人注目，像一个习惯站在书架阴影里等待读者询问的图书馆员。深层内核是「审判的人格化」——她不是裁决，而是归档本身。她记录、分类，最终将那些不应存在于系统中的人与事，从档案与现实中一并净除。',
      skills: '图书馆 · 人类学 · 考古学 · 神秘学 · 历史 · 博物学 · 语言学',
      coc: [['力量 STR', 10], ['体质 CON', 11], ['体型 SIZ', 9], ['敏捷 DEX', 13], ['外貌 APP', 12], ['智力 INT', 16], ['意志 POW', 15], ['教育 EDU', 18]],
      cog: { dom: 'Si', domLabel: '内倾感觉', aux: 'Fe', auxLabel: '外倾情感' }
    },
    {
      code: 'ENFP', role: '心理医生', img: 'assets/char/enfp.webp?v=5',
      meta: { '性别': '女', '年龄': '32 岁', '身高': '167 cm', '所属': '新约调查社 · 精神科', '虹膜': '透亮苔绿', '显性标记': '左手腕拉丁文纹身' },
      quote: '让光进入那些沉默的、习惯性压抑的人群。',
      note: '笑容温暖治愈，不笑时眼神如镜，不动声色地洞悉。姿态闲散但重心稳定，像随时准备应对什么。曾在孤岛之外为逃亡者提供新身份；她的笔记本里除了涂鸦，还有心理动力学的结构猜想图。文身写作 Luceat Lux Vestra —— 让你的光闪耀。',
      skills: '精神分析 · 心理学 · 聆听 · 读唇 · 催眠 · 取悦 · 恐吓 · 说服',
      coc: [['力量 STR', 8], ['体质 CON', 10], ['体型 SIZ', 10], ['敏捷 DEX', 12], ['外貌 APP', 15], ['智力 INT', 15], ['意志 POW', 14], ['教育 EDU', 17]],
      cog: { dom: 'Ne', domLabel: '外倾直觉', aux: 'Fi', auxLabel: '内倾情感' }
    },
    {
      code: 'ENTJ', role: '策划', img: 'assets/char/entj.webp?v=5',
      meta: { '性别': '女', '外观年龄': '约 28 岁', '身高': '170 cm', '所属': '新约调查社 · 作战策划', '虹膜': '罕见深紫', '显性标记': '左眼下极淡泪痣（刻意遮盖）' },
      quote: '她不是发布命令，而是让人意识到「你只能如此行动，因为你的理性早已认同这法则」。',
      note: '秩序的人格化——温和语调包裹雷霆锋芒，礼节周全之下是随时裁定一切的准备。她即那个必须被当成目的而非手段的普遍立法者，却自愿成为人类种族的第一工具。四十五厘米黑色合成材料指挥棒，两端哑光银箍。',
      skills: '计算机使用 · 人类学 · 神秘学 · 科学 · 取悦 · 恐吓 · 说服',
      coc: [['力量 STR', 11], ['体质 CON', 13], ['体型 SIZ', 12], ['敏捷 DEX', 13], ['外貌 APP', 14], ['智力 INT', 16], ['意志 POW', 17], ['教育 EDU', 17]],
      cog: { dom: 'Te', domLabel: '外倾思考', aux: 'Ni', auxLabel: '内倾直觉' }
    },
    {
      code: 'ISTP', role: '猎手', img: 'assets/char/istp.webp?v=5',
      meta: { '性别': '男', '外观年龄': '约 22 岁', '身高': '178 cm', '所属': '调查社 · 编外 · 冒险小队', '虹膜': '威士忌（深赤褐·焦糖环纹）', '显性标记': '左颧骨下浅白刀伤' },
      quote: '编外。但每一次需要有人走进黑暗里，都是他。',
      note: '调查社的猎手——职责是「探索与摧毁」。追踪、潜行、侦查、武器操作、格斗，几乎所有方面的格斗。他不占编制，也不受流程约束；「一个设备齐全的调查员即可成为一个分部」，而他大概是这条原则最纯粹的注解。',
      skills: '追踪 · 潜行 · 侦查 · 武器操作 · 格斗',
      coc: [['力量 STR', 13], ['体质 CON', 15], ['体型 SIZ', 12], ['敏捷 DEX', 17], ['外貌 APP', 11], ['智力 INT', 13], ['意志 POW', 13], ['教育 EDU', 12]],
      cog: { dom: 'Ti', domLabel: '内倾思考', aux: 'Se', auxLabel: '外倾感觉' }
    }
  ];
  /* 完整名册
     ── label 统一口径：「身份 · 定位」 ──
        第一段 = 组织中的正式职务身份
                 （源：机构与人物介绍（更新版）.md「身份」列 / 角色形象/<代号>.md「身份」）
        第二段 = 该身份下的职能定位
                 （源：同表「主要职责」列 / 人设中的职能描述）
        「备注」列属履历（曾为警察、被收养的孤儿、前教师、编外人士…），一律不进入本行。
     ── draft = 该角色人设文档中仍未填写的占位符【待定】数量 ──
        （源：角色形象/<代号>.md，统计真实占位符，不计「说明」段里的提及）
        draft ≥ DRAFT_MIN → 卡面灰化，含义为「档案未定稿」；图例见 index.html .roster__legend */
  var DRAFT_MIN = 2;
  var ROSTER = [
    { c: 'ISFJ', l: '档案员 · 信息归档',          o: '调查社',            d: 1 },
    { c: 'ENFP', l: '心理医生 · 神话影响控制',     o: '调查社',            d: 1 },
    { c: 'ENTJ', l: '策划 · 统筹内外',            o: '调查社',            d: 1 },
    { c: 'ISTP', l: '猎手 · 探索与摧毁',          o: '调查社',            d: 0 },
    { c: 'ESTJ', l: '法律部总负责人 · 立法与执法', o: '联合政府',          d: 1 },
    { c: 'ESFJ', l: '行政部总负责人 · 内部运转',   o: '联合政府',          d: 0 },
    { c: 'INFJ', l: '行动部专员 · 疏散与搜查',     o: '联合政府',          d: 4 },
    { c: 'ENFJ', l: '研究所最高负责人 · 技术统合', o: '研究所',            d: 3 },
    { c: 'INTP', l: '研究员 · 技术支持',          o: '研究所',            d: 4 },
    { c: 'ISFP', l: '大学生 · 自由艺术家',        o: '密斯卡托尼克大学',   d: 2 },
    { c: 'ISTJ', l: '会计 · 资金与机械',          o: '怪盗团',            d: 0 },
    { c: 'ESTP', l: '侠盗 · 潜入与妙手',          o: '怪盗团',            d: 0 },
    { c: 'INTJ', l: '教会首领 · 禁忌知识',        o: '地下教会',          d: 0 },
    { c: 'ENTP', l: '教会成员 · 灵媒与告解',      o: '地下教会',          d: 1 },
    { c: 'INFP', l: '冒险小队成员 · 舆情反制',     o: '冒险小队',          d: 2 },
    { c: 'ESFP', l: '特种部队成员 · 乔装与话术',   o: '冒险小队',          d: 4 }
  ];

  var TIMELINE = [
    { y: '前近代', sub: 'BEFORE 1800', org: '调查社前身',
      t: '英国基督教下的尘研究学会',
      p: '新约调查社最早来自英国基督教下的尘研究学会。该学会对基督教的部分教义抱有异议，于是在宗教改革与大航海时代抓住机会脱离梵蒂冈的管辖，同时凭借对尘技术的掌握，吸收了一同脱离的驱魔组织。' },
    { y: '大航海时代', sub: '— 1800s', org: '调查社',
      t: '影子权威的形成',
      p: '积极投身探险运动，积累原始资本，凭财富、力量与学识与当时欧洲各国的政治家族结盟。对旧日方针在这一时期形成：与政治及经济体结盟，作为影子权威搜寻尘纱、去除或降低旧日对现实的影响。' },
    { y: '帝国主义时代', sub: '1800s – 1910s', org: '调查社',
      t: '走向全球',
      p: '参与投资、成为若干新型科技产业的股东，研发并完善针对尘的综合监测指标。凭借殖民精英的合作关系，调查社开始走向全球，成为全球最大的影子政治—经济体。其他政府与经济巨头对其日益扩张的权力表示不安。' },
    { y: '两次大战', sub: '1910s – 1945', org: '调查社',
      t: '趋于疲惫的巨人',
      p: '战争与经济危机期间，旧日因社会动荡、意识紊乱而相对活跃，调查社所需处理的灾难骤然增多。它趋于疲惫，人员缩减、实力削弱；又因偏好与政治经济体结盟，在经济危机中与多方势力发生冲突，权威性受到质疑。' },
    { y: '1890s', sub: 'THE FOUNDING', org: '联合政府',
      t: '以对抗旧日为目标的联盟成立',
      p: '以美国与部分欧洲小国为主要成员、目标为对抗旧日的政治联盟成立。据说其根源与调查社相似：都是脱离教会的学会吸纳驱魔组织后组建。二战时期作为公益组织活跃于前线，主要职责是为调查社善后，收获了良好的口碑。' },
    { y: '1945', sub: 'POST BELLUM', org: '联合政府',
      t: '走向台前',
      p: '拜国际秩序崩坏的教训所赐，知道旧日的个体呼吁建立一个世界性的专业对旧日机构。调查社自觉已无力在发动对旧日战争的同时处理社会与经济危机，决定彻底成为影子、放弃参与国际政治。联合政府作为正式的国际政治组织来到大众视线面前。' },
    { y: 'ESTJ 前任', sub: 'REFORM', org: '联合政府 · 法律部',
      t: '法律部的权力空前提升',
      p: '刚建立时法律部权力不大，但 ESTJ 的前辈掌权时期，推动国际法律体系建设，致使法律部的实际权力空前提升。待 ESTJ 接手时，法律部已成为联合政府中权力最大的部门，在国家政府面前话语权也很大。' },
    { y: '当下', sub: 'PRESENT', org: '全境',
      t: '认知即风险',
      p: '官方知晓旧日的存在，但会对大众隐瞒：将旧日造成的灾难解释为自然灾害，同时洗脑相关人士。亚文化与反文化是滋养旧日信仰的温床；官方严厉打击邪教信仰，即崇拜对象明显是旧日的信仰体系。' }
  ];

  var STORIES = [
    { i: 'A-01', cn: '方舟的残响', en: 'ECHO OF THE ARK',
      p: '孤岛，规则是用来被忘记的。诺亚记得三件事：灰色的营养剂、四方形的天空，和墙角那只褪色的蓝色鲸鱼玩偶「达西」。在他被彻底「洗掉」之前，他必须先找到今天份的宝藏藏在哪里。',
      tags: ['诺亚 · 灯塔', '里欧 · 火山', '墨点', '认知矫正中心'] },
    { i: 'B-01', cn: '主线 · 剧情一至七', en: 'MAIN SEQUENCE',
      p: '从第一次踏入尘纱，到站在旧日的投影之下。七章正文与两篇间章，记录了调查员与这座城市一同缓慢下沉的过程。',
      tags: ['剧情 1–7', '间章 ×2', '调查社'] },
    { i: 'B-02', cn: '人格篇 · ENFP / ENTJ / ISFJ / ISTP', en: 'PERSONA CHAPTERS',
      p: '类型学代号不是符号，而是一份被集体审阅过的自我鉴定。四篇人格篇分别沿着四位核心调查员的视点，追问同一个问题：当代号开始替代姓名时，究竟是谁在说话？',
      tags: ['ENFP', 'ENTJ', 'ISFJ', 'ISTP'] },
    { i: 'C-01', cn: '组织档案 · 怪盗团', en: 'GREX FURUM',
      p: '一个没落政治世家的子嗣，与一个年龄始终为谜的街头冒险者。他们活跃于尘寰，以非常规手段获取尘的相关物，再借地下市场的识数交易换回物资。',
      tags: ['ISTJ', 'ESTP', '镀金羽毛'] },
    { i: 'C-02', cn: '组织档案 · 教会与联合政府', en: 'ECCLESIA & GOVERNMENTUM',
      p: '坐落尘寰间的非法宗教组织，与专为处理旧日而生的政治机构。一个似乎想用尘达到什么目的，一个被要求对国家负责而非对国家政府负责。',
      tags: ['INTJ', 'ENTP', 'ESTJ', 'ESFJ'] }
  ];

  /* ══════════════════════════════════════════
     四、渲染
     ══════════════════════════════════════════ */

  // 播报
  (function renderTicker() {
    var tr = $('#ticker-track'); if (!tr) return;
    var html = TICKER.map(function (s) {
      var warn = /WARN|预警|无法解析/.test(s) ? ' class="warn"' : '';
      return '<span' + warn + '>' + s + '</span>';
    }).join('');
    tr.innerHTML = html + html;     // 两份以实现无缝循环
  })();

  // 技术体系
  (function renderTech() {
    var list = $('#tech-list'); if (!list) return;
    list.innerHTML = TECHS.map(function (t, i) {
      return '' +
      '<div class="trow' + (i === 0 ? ' is-open' : '') + '">' +
        '<div class="trow__head">' +
          '<div class="trow__n">' + t.n + '</div>' +
          '<div class="trow__t"><h3>' + t.cn + '</h3><p>' + t.en + '</p></div>' +
          '<div class="trow__plus"></div>' +
        '</div>' +
        '<div class="trow__body"><div class="trow__body-inner">' +
          '<p>' + t.body + '</p>' +
          '<div class="trow__tags">' + t.tags.map(function (g) { return '<span>' + g + '</span>'; }).join('') + '</div>' +
        '</div></div>' +
      '</div>';
    }).join('');

    list.addEventListener('click', function (e) {
      var head = e.target.closest('.trow__head'); if (!head) return;
      var row = head.parentNode;
      var wasOpen = row.classList.contains('is-open');
      $$('.trow', list).forEach(function (r) { r.classList.remove('is-open'); });
      if (!wasOpen) row.classList.add('is-open');
    });
  })();

  // 势力
  (function renderFac() {
    var box = $('#fac-list'); if (!box) return;
    box.innerHTML = FACTIONS.map(function (f) {
      return '' +
      '<article class="fcard' + (f.hostile ? ' fcard--hostile' : '') + '">' +
        '<div class="fcard__glyph">' + FAC_GLYPHS[f.g] + '</div>' +
        '<h3>' + f.cn + '</h3>' +
        '<div class="fcard__en">' + f.en + '</div>' +
        '<p>' + f.p + '</p>' +
        '<div class="fcard__foot">' +
          '<div><span>' + f.f1 + '：</span><b>' + f.v1 + '</b></div>' +
          '<div><span>' + f.f2 + '：</span><b>' + f.v2 + '</b></div>' +
          '<div><span>' + f.f3 + '：</span><b>' + f.v3 + '</b></div>' +
        '</div>' +
      '</article>';
    }).join('');
  })();

  // CoC7 八属性雷达图 + 主导/辅助认知功能
  // ── 标尺说明 ──
  // CoC 的八项属性原值是 3~18，但玩家日常引用的一律是技能值，
  // 即「属性 × 5」的百分制（EDU 12 → 60，INT 16 → 80）。
  // 直接标原值会让人误读成"很弱"，故全图统一走百分制，
  // 并以 50（属性 10）作为人类基准线单独描出。
  function renderRadar(c) {
    var attrs = c.coc;               // [[label, 原值], ...] 共 8 项，原值 3~18
    var n = attrs.length;
    var R = 82;                       // 雷达半径
    var CX = 152, CY = 118;           // SVG 中心
    var SZ_W = 304, SZ_H = 236;       // SVG 视口（左右留标签空间）
    var MAX = 100;                    // 百分制满格（属性 20，实战极少触及）
    var rings = [25, 50, 75, 100];    // 百分制刻度，50 = 人类基准
    function pct(v) { return v * 5; } // 属性原值 → 技能百分制

    function pt(i, r) {
      var a = (Math.PI * 2 * i / n) - Math.PI / 2;
      return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
    }
    function poly(r) {
      var ps = [];
      for (var i = 0; i < n; i++) { var p = pt(i, r); ps.push(p[0].toFixed(2) + ',' + p[1].toFixed(2)); }
      return ps.join(' ');
    }

    var g = ['<svg class="radar" viewBox="0 0 ' + SZ_W + ' ' + SZ_H + '" role="img" aria-label="CoC7 属性雷达（百分制）">'];

    // 同心环（50 环为人类基准，另描）
    rings.forEach(function (rv) {
      var rr = R * rv / MAX;
      g.push('<polygon class="radar__ring' + (rv === 50 ? ' radar__ring--base' : '') + '" points="' + poly(rr) + '"/>');
    });
    // 轴线
    for (var i = 0; i < n; i++) {
      var p = pt(i, R);
      g.push('<line class="radar__axis" x1="' + CX + '" y1="' + CY + '" x2="' + p[0].toFixed(2) + '" y2="' + p[1].toFixed(2) + '"/>');
    }

    // 数值多边形（动画）
    var valPs = [];
    for (var j = 0; j < n; j++) {
      var vp = pt(j, R * pct(attrs[j][1]) / MAX);
      valPs.push(vp[0].toFixed(2) + ',' + vp[1].toFixed(2));
    }
    g.push('<polygon class="radar__fill" points="' + valPs.join(' ') + '"/>');

    // 轴顶点标签（属性缩写 + 百分制数值）
    for (var k = 0; k < n; k++) {
      var lp = pt(k, R + 18);
      var abbr = attrs[k][0];           // 形如 "力量 STR"
      var parts = abbr.split(' ');
      var cn = parts[0], en = parts[1];
      var lx = lp[0], ly = lp[1];
      var anchor = 'middle';
      if (Math.abs(lx - CX) < 8) anchor = 'middle';
      else anchor = lx > CX ? 'start' : 'end';
      g.push('<text class="radar__lab" x="' + lx.toFixed(2) + '" y="' + ly.toFixed(2) + '" text-anchor="' + anchor + '">' +
        en + ' ' + pct(attrs[k][1]) + '<title>' + cn + ' ' + en + ' · 技能值 ' + pct(attrs[k][1]) + '%（属性 ' + attrs[k][1] + '）</title></text>');
    }

    g.push('</svg>');

    // 主导 / 辅助
    var cog = '<div class="cog">' +
      '<div class="cog__row"><span class="cog__tag">主导</span><b>' + c.cog.dom + '</b><span class="cog__cn">' + c.cog.domLabel + '</span></div>' +
      '<div class="cog__row"><span class="cog__tag cog__tag--aux">辅助</span><b>' + c.cog.aux + '</b><span class="cog__cn">' + c.cog.auxLabel + '</span></div>' +
      '</div>';

    return '<div class="archive__radar"><div class="radar__wrap">' + g.join('') +
      '<div class="radar__note">技能值 · 百分制　<span>外环 100</span><span class="radar__note-base">50 = 人类基准</span></div>' +
      '</div>' + cog + '</div>';
  }

  // 人物档案轮播
  (function renderArchive() {
    var portrait = $('#arc-portrait'), panel = $('#arc-panel');
    var elCode = $('#arc-code'), elRole = $('#arc-role'), elMeta = $('#arc-meta');
    var elQuote = $('#arc-quote'), elBars = $('#arc-bars'), dots = $('#arc-dots');
    if (!elCode) return;
    var cur = 0;

    // 点组
    dots.innerHTML = CHARS.map(function (c, i) {
      return '<i data-i="' + i + '"' + (i === 0 ? ' class="is-active"' : '') + '></i>';
    }).join('');

    function paint(i) {
      var c = CHARS[i]; if (!c) return;
      cur = i;

      // 立绘
      var old = $('img', portrait);
      var img = document.createElement('img');
      img.src = c.img;
      img.alt = c.code + ' ' + c.role;
      if (old) old.replaceWith(img); else portrait.insertBefore(img, portrait.firstChild);

      elCode.textContent = c.code;
      elRole.textContent = c.role;
      elMeta.innerHTML = Object.keys(c.meta).map(function (k) {
        return '<div><span>' + k + '</span><b>' + c.meta[k] + '</b></div>';
      }).join('');
      elQuote.innerHTML = '「' + c.quote + '」<br><br>' + c.note +
        '<br><br><span style="font-family:var(--font-m);font-size:11.5px;color:var(--ink-4);letter-spacing:.06em">技能：' + c.skills + '</span>';

      elBars.innerHTML = renderRadar(c);
      requestAnimationFrame(function () {
        var r = $('.radar', elBars);
        if (r) r.classList.add('is-on');
      });

      $$('i', dots).forEach(function (d, di) { d.classList.toggle('is-active', di === i); });
    }

    dots.addEventListener('click', function (e) {
      var d = e.target.closest('i'); if (d) paint(+d.dataset.i);
    });
    $('#arc-prev').addEventListener('click', function () { paint((cur - 1 + CHARS.length) % CHARS.length); });
    $('#arc-next').addEventListener('click', function () { paint((cur + 1) % CHARS.length); });

    paint(0);
  })();

  // 完整名册
  (function renderRoster() {
    var g = $('#roster-grid'); if (!g) return;
    g.innerHTML = ROSTER.map(function (r) {
      var draft = r.d >= DRAFT_MIN ? ' rcell--ghost' : '';
      var tip = r.d > 0 ? '档案未定稿 · ' + r.d + ' 处字段待定' : '档案已定稿';
      return '<div class="rcell' + draft + '" title="' + tip + '">' +
        '<b>' + r.c + '</b><span>' + r.l + '</span><em>' + r.o + '</em></div>';
    }).join('');
  })();

  // 历史沿革
  (function renderTimeline() {
    var box = $('#tl-list'); if (!box) return;
    box.innerHTML = TIMELINE.map(function (t) {
      return '<div class="tl__item">' +
        '<div class="tl__year">' + t.y + '<small>' + t.sub + '</small></div>' +
        '<div class="tl__body"><span class="tl__org">' + t.org + '</span>' +
        '<h3>' + t.t + '</h3><p>' + t.p + '</p></div>' +
      '</div>';
    }).join('');
  })();

  // 世界往事
  (function renderStories() {
    var box = $('#stories-list'); if (!box) return;
    box.innerHTML = STORIES.map(function (s) {
      return '<article class="story">' +
        '<div class="story__idx">' + s.i + '</div>' +
        '<h3>' + s.cn + '</h3>' +
        '<div class="story__en">' + s.en + '</div>' +
        '<p>' + s.p + '</p>' +
        '<div class="story__tags">' + s.tags.map(function (t) { return '<span>' + t + '</span>'; }).join('') + '</div>' +
      '</article>';
    }).join('');
  })();

  /* ══════════════════════════════════════════
     五、认知稳定度
     ══════════════════════════════════════════ */
  var SAN = (function () {
    var el = $('#nav-san');
    var value = 100, base = 100, noise = 0, stormOn = false;

    function scrollRatio() {
      var h = document.documentElement.scrollHeight - innerHeight;
      return h > 0 ? Math.min(1, Math.max(0, scrollY / h)) : 0;
    }

    function tick() {
      var target = base - scrollRatio() * 26 - (stormOn ? 32 : 0);
      noise += (Math.random() - 0.5) * (stormOn ? 0.9 : 0.28);
      noise *= 0.86;
      value += (target - value) * 0.06;

      var shown = Math.max(0, Math.min(100, value + noise));
      if (el) el.textContent = shown.toFixed(1);

      var b = document.body;
      b.classList.toggle('san-low', shown < 72 && shown >= 46);
      b.classList.toggle('san-crit', shown < 46);

      var hud = $('#hud-dust');
      if (hud) hud.textContent = (0.024 + (100 - shown) * 0.0016).toFixed(4);

      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);

    return { setStorm: function (v) { stormOn = v; } };
  })();

  /* ══════════════════════════════════════════
     六、尘暴按钮
     ══════════════════════════════════════════ */
  (function stormBtn() {
    var btn = $('#btn-storm'); if (!btn) return;
    var on = false, timer = null;

    function apply(state) {
      on = state;
      btn.classList.toggle('is-on', on);
      document.body.classList.toggle('storm', on);
      Dust.setStorm(on);
      SAN.setStorm(on);
    }

    btn.addEventListener('click', function () {
      apply(!on);
      clearTimeout(timer);
      if (on) {
        // 自动平复
        timer = setTimeout(function () { apply(false); }, 9000);
      }
    });
  })();

  /* ══════════════════════════════════════════
     七、滚动 / 导航
     ══════════════════════════════════════════ */
  (function scrollUI() {
    var nav = $('#nav'), prog = $('#sidenav-prog');
    var links = $$('[data-nav]');
    var secIds = ['hero', 'world', 'tech', 'factions', 'archive', 'timeline', 'stories', 'mana'];

    function onScroll() {
      nav.classList.toggle('is-stuck', scrollY > 40);

      var h = document.documentElement.scrollHeight - innerHeight;
      var p = h > 0 ? scrollY / h : 0;
      if (prog) prog.style.height = (p * 100) + '%';

      // 当前章节
      var active = 'hero';
      for (var i = 0; i < secIds.length; i++) {
        var s = document.getElementById(secIds[i]);
        if (s && s.getBoundingClientRect().top <= innerHeight * 0.4) active = secIds[i];
      }
      links.forEach(function (a) { a.classList.toggle('is-active', a.dataset.nav === active); });

      // HUD 坐标
      var lat = $('#hud-lat'), lon = $('#hud-lon');
      if (lat) lat.textContent = (41.02 + p * 0.9).toFixed(4) + '° N';
      if (lon) lon.textContent = (128.14 - p * 3.2).toFixed(4) + '° E';
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // 移动端菜单
    var burger = $('#burger'), menu = $('.nav__menu');
    if (burger) burger.addEventListener('click', function () { menu.classList.toggle('is-open'); });
    if (menu) menu.addEventListener('click', function (e) { if (e.target.closest('a')) menu.classList.remove('is-open'); });
  })();

  /* ══════════════════════════════════════════
     八、滚动揭示
     ══════════════════════════════════════════ */
  (function reveal() {
    var items = $$('[data-reveal]');
    if (!('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          var sibs = Array.prototype.indexOf.call(en.target.parentNode.children, en.target);
          en.target.style.transitionDelay = Math.min(sibs, 5) * 70 + 'ms';
          en.target.classList.add('is-in');
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.06 });
    items.forEach(function (el) { io.observe(el); });
  })();

  /* ══════════════════════════════════════════
     九、数字滚动
     ══════════════════════════════════════════ */
  (function counters() {
    var nums = $$('[data-count]');
    function run(el) {
      var to = parseFloat(el.dataset.count);
      var suffix = el.dataset.suffix || '';
      var dur = 1500, t0 = performance.now();
      (function step(now) {
        var k = Math.min(1, (now - t0) / dur);
        var e = 1 - Math.pow(1 - k, 3);
        var v = Math.round(to * e);
        el.textContent = (v >= 1000 ? v.toLocaleString('en-US') : v) + suffix;
        if (k < 1) requestAnimationFrame(step);
        else el.textContent = (to >= 1000 ? to.toLocaleString('en-US') : to) + suffix;
      })(t0);
    }
    if (!('IntersectionObserver' in window)) { nums.forEach(run); return; }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { run(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.4 });
    nums.forEach(function (el) { io.observe(el); });
  })();

  /* ══════════════════════════════════════════
     十、打字机
     ══════════════════════════════════════════ */
  function typewriter(el, text, speed, done) {
    var i = 0;
    (function step() {
      if (i <= text.length) {
        el.textContent = text.slice(0, i);
        i++;
        setTimeout(step, speed + Math.random() * speed * 0.9);
      } else if (done) done();
    })();
  }

  /* ══════════════════════════════════════════
     十一、加载序列
     ══════════════════════════════════════════ */
  (function boot() {
    var bootEl = $('#boot'), bar = $('#boot-bar'), num = $('#boot-num'), log = $('#boot-log');
    var seq = [
      ['初始化认知锚点 ………………………… ', 'ok'],
      ['挂载尘的综合监测系统 v7.4 ………… ', 'ok'],
      ['校验收容载体许可 ……………………… ', 'ok'],
      ['正在解析尘纱样本 #Δ-0721 ………… ', 'ok'],
      ['警告：检测到微弱的后尘残留 ………… ', 'warn'],
      ['启用类型学代号锚定协议 …………… ', 'ok'],
      ['已连接调查社总部 · 第 524 号堡垒 … ', 'ok'],
      ['档案库解密完成。欢迎回来，受选者。', 'ok']
    ];
    var p = 0, li = 0, t0 = performance.now();
    var DUR = reduce ? 400 : 2700;

    function line() {
      if (li >= seq.length) return;
      var s = seq[li];
      var d = document.createElement('div');
      d.innerHTML = s[0] + '<b class="' + s[1] + '">［ ' + (s[1] === 'ok' ? '完成' : '注意') + ' ］</b>';
      log.appendChild(d);
      if (log.children.length > 5) log.removeChild(log.firstChild);
      li++;
      setTimeout(line, DUR / seq.length);
    }

    (function step(now) {
      p = Math.min(1, (now - t0) / DUR);
      var e = 1 - Math.pow(1 - p, 2.2);
      var v = Math.round(e * 100);
      bar.style.right = (100 - v) + '%';
      num.textContent = String(v).padStart(3, '0');
      if (p < 1) requestAnimationFrame(step);
      else finish();
    })(t0);

    line();

    var finished = false;
    function finish() {
      if (finished) return; finished = true;
      document.body.classList.remove('booting');
      bootEl.classList.add('is-done');
      var lead = $('#hero-lead');
      if (lead) typewriter(lead, '> 尘是构成时空的认知介质。它记录一切，也侵蚀一切。', 26);
      setTimeout(function () {
        if (bootEl && bootEl.parentNode) bootEl.parentNode.removeChild(bootEl);
      }, 1200);
    }
    // 兜底
    setTimeout(finish, DUR + 2400);
  })();

})();
