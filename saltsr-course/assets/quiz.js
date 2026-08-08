/* =========================================================================
   quiz.js — 分階測驗（題數由 STAGES 自動計算）
   每題：即時回饋、指出該複習哪個單元、自動計分
   ========================================================================= */
(function () {
  'use strict';

  const L = (u, t) => `<a href="lesson.html#u${u}">單元 ${String(u).padStart(2, '0')}：${t}</a>`;

  const STAGES = [
    {
      title: '階段 1 · 鹽害背景與 R 基礎',
      sub: '單元 00–02。看懂問題、看懂第一行程式。',
      qs: [
        { q: '古蹟牆體裡的可溶鹽，最主要的來源機制是什麼？',
          o: ['地下水沿毛細孔上升，蒸發後把鹽留在牆體',
              '建材在窯燒過程中自然生成',
              '空氣中的水氣直接凝結成鹽',
              '陽光照射使材料表面分解'],
          a: 0,
          e: '毛細上升（rising damp）把地下水和溶在裡面的鹽帶進牆體，水在牆面蒸發、鹽留下。幾十年下來就在牆體下段累積。',
          r: [0, '鹽為什麼會把牆吃掉'] },

        { q: '下列哪一項<strong>不是</strong>鹽破壞多孔材料的主要機制？',
          o: ['結晶壓：鹽晶體在孔隙中長大並推擠孔壁',
              '潮解／再結晶循環：反覆溶解與析出',
              '水合膨脹：例如 Na₂SO₄ 吸水變成 Na₂SO₄·10H₂O',
              '酸鹼中和：鹽與碳酸鈣反應產生氣體撐裂材料'],
          a: 3,
          e: '前三項是公認的三大機制。酸鹼中和產氣不是鹽風化的主要途徑 —— 鹽害本質上是物理性的（壓力），不是化學溶蝕。',
          r: [0, '鹽為什麼會把牆吃掉'] },

        { q: '「潮解相對濕度（DRH）」指的是什麼？',
          o: ['鹽開始從空氣中吸水、自發變成溶液的臨界濕度',
              '空氣中水氣達到飽和的濕度',
              '材料本身開始吸水的濕度',
              '鹽完全脫水變成無水物的濕度'],
          a: 0,
          e: '環境濕度高於 DRH，鹽吸水溶解；低於它，鹽結晶析出。所以 DRH 是把「濕度」和「破壞」連起來的關鍵參數。',
          r: [0, '鹽為什麼會把牆吃掉'] },

        { q: '為什麼「混合鹽比純鹽危險」？',
          o: ['混合鹽的潮解點低於任何單一組分，因此更容易跨越臨界值、循環更頻繁',
              '混合鹽的晶體比純鹽硬',
              '混合鹽的分子量比較大',
              '混合鹽會產生額外的化學反應熱'],
          a: 0,
          e: '離子之間的交互作用降低水的活性，使混合物的潮解點低於任一單組分（Rörig-Dalgaard 2021）。臨界點被拉低，在同樣的氣候波動下被跨越的次數就更多。',
          r: [0, '鹽為什麼會把牆吃掉'] },

        { q: '在 R 裡，下列哪一行會把 1.128 存進名為 <code>dry_g</code> 的變數？',
          o: ['<code>dry_g &lt;- 1.128</code>',
              '<code>dry_g == 1.128</code>',
              '<code>1.128 -&gt; dry_g()</code>',
              '<code>var dry_g = 1.128</code>'],
          a: 0,
          e: '<code>&lt;-</code> 是 R 的指派運算子。<code>==</code> 是「判斷是否相等」，<code>var</code> 是 JavaScript 的語法。',
          r: [1, 'R 的第一行'] },

        { q: '執行 <code>Dry_g &lt;- 1.0</code> 之後再執行 <code>dry_g</code>，會發生什麼？',
          o: ['出現 <code>object \'dry_g\' not found</code> 錯誤，因為 R 區分大小寫',
              '印出 1.0，R 不區分大小寫',
              '印出 NULL',
              '自動建立一個值為 0 的新變數'],
          a: 0,
          e: 'R 嚴格區分大小寫，<code>Dry_g</code> 和 <code>dry_g</code> 是兩個不同的名字。這是初學者最常見的錯誤來源之一。',
          r: [1, 'R 的第一行'] },

        { q: '<code>ppm &lt;- c(50, 30, 20)</code> 之後執行 <code>ppm * 2</code>，結果是什麼？',
          o: ['<code>100 60 40</code> —— 每個元素都乘以 2',
              '<code>200</code> —— 總和乘以 2',
              '<code>50 30 20 50 30 20</code> —— 向量重複兩次',
              '錯誤，向量不能直接乘以數字'],
          a: 0,
          e: '這就是「向量化運算」：算術運算自動作用在向量的每一個元素上。這個特性讓你能用一行取代七行。',
          r: [2, '向量、資料框與管線'] },

        { q: '要從資料框 <code>samples</code> 取出 <code>chloride_ppm</code> 這一整欄，正確的寫法是？',
          o: ['<code>samples$chloride_ppm</code>',
              '<code>samples.chloride_ppm</code>',
              '<code>samples-&gt;chloride_ppm</code>',
              '<code>samples[chloride_ppm]</code>'],
          a: 0,
          e: 'R 用 <code>$</code> 取資料框的欄位。<code>.</code> 在 R 裡只是普通字元，不是取成員的運算子。',
          r: [2, '向量、資料框與管線'] }
      ]
    },

    {
      title: '階段 2 · 單位換算',
      sub: '單元 03–04。從 ppm 到 wt% 到 mEq/kg，以及為什麼要換。',
      qs: [
        { q: '離子層析測到的 ppm 是「萃取液」的濃度。為什麼一定要換算成占乾樣重的百分比？',
          o: ['因為同樣的濃度，若來自不同的樣品量，代表的鹽害程度完全不同',
              '因為 ppm 這個單位不夠精確',
              '因為熱力學模型只接受百分比',
              '因為 ppm 會隨溫度改變'],
          a: 0,
          e: '1 g 樣品配 100 mL 測到 50 ppm，和 5 g 樣品配 100 mL 測到 50 ppm，後者的牆乾淨得多。必須正規化到乾樣重才能比較。',
          r: [3, '從 ppm 到重量百分比'] },

        { q: '乾重 1.000 g、水量 100 mL、氯離子 50 ppm，用式 1 算出的重量百分比是？',
          o: ['0.50 wt%', '0.05 wt%', '5.0 wt%', '50 wt%'],
          a: 0,
          e: '(50 × 100) / (10000 × 1.000) = 0.50。也就是這塊磚有 0.5 % 的重量是氯離子。',
          r: [3, '從 ppm 到重量百分比'] },

        { q: '同樣的樣品，如果實驗室助理把乾重誤記成 10.00 g（多了一個零），算出來的鹽含量會怎樣？',
          o: ['變成原本的 1/10，嚴重低估鹽害',
              '變成原本的 10 倍，嚴重高估鹽害',
              '不受影響，因為乾重會被消掉',
              '只影響 mEq/kg，不影響 wt%'],
          a: 0,
          e: '乾重在分母，變成 10 倍就會讓結果變成 1/10。這種錯誤在最終判讀上可能讓一面「該立即處理」的牆被判成「正常」。',
          r: [3, '從 ppm 到重量百分比'] },

        { q: '談電荷平衡時，為什麼不能直接用莫耳，而要用「當量」？',
          o: ['因為 1 莫耳 Ca²⁺ 帶的電荷是 1 莫耳 Na⁺ 的兩倍，用莫耳會低估雙價離子',
              '因為莫耳這個單位太大',
              '因為當量比較好計算',
              '因為離子層析只能測當量'],
          a: 0,
          e: '當量 = 莫耳 × 電荷數 z。換成當量之後，任何離子的 1 Eq 都帶同樣多的電荷，才能直接相加相減。',
          r: [4, '當量濃度 mEq/kg'] },

        { q: 'SO₄²⁻ 的分子量是 96.064、電荷數是 2，它的當量重是多少？',
          o: ['48.03 g/Eq', '96.06 g/Eq', '192.13 g/Eq', '2.00 g/Eq'],
          a: 0,
          e: '當量重 = M / z = 96.064 / 2 = 48.03 g/Eq。當量重越小，同樣 ppm 換算出的當量越大。',
          r: [4, '當量濃度 mEq/kg'] },

        { q: '在七個離子中，哪一個的當量重最小，因此「同樣 1 ppm 貢獻的電荷最多」？',
          o: ['Mg²⁺（12.15 g/Eq）', 'Na⁺（22.99 g/Eq）', 'Cl⁻（35.45 g/Eq）', 'NO₃⁻（62.00 g/Eq）'],
          a: 0,
          e: '鎂的分子量小（24.305）又是雙價，當量重只有 12.15。這解釋了為什麼鎂的 ppm 看起來很小，在電荷平衡表上卻很有份量。',
          r: [4, '當量濃度 mEq/kg'] },

        { q: 'MH-01 的陰離子 ppm 總和是 100、陽離子是 70，但換算成 mEq/kg 之後陰離子 231、陽離子 316。這說明了什麼？',
          o: ['ppm 的大小關係不能用來判斷電荷平衡，換單位後結論可能完全相反',
              '計算一定出錯了',
              '離子層析的數據不可靠',
              '陽離子的分子量比較大'],
          a: 0,
          e: '這正是本課程最重要的觀念之一：<strong>電荷平衡必須在當量的尺度上判斷</strong>，用 ppm 或 wt% 目測會得到相反的結論。',
          r: [4, '當量濃度 mEq/kg'] },

        { q: '「吸濕含水率（HMC）」為什麼可以當成鹽含量的快速篩檢指標？',
          o: ['因為在 95 %RH 下吸水的主要是鹽而不是材料本身，HMC 高就代表鹽多',
              '因為 HMC 直接測量鹽的重量',
              '因為材料的吸水能力與鹽無關',
              '因為 HMC 只在有硫酸鹽時才會升高'],
          a: 0,
          e: 'HMC 只要秤重就能得到，不需要離子層析。它是現場快篩很好用的指標，但無法告訴你是哪些鹽 —— 那還是得靠 IC。',
          r: [4, '當量濃度 mEq/kg'] }
      ]
    },

    {
      title: '階段 3 · 電荷平衡與石膏',
      sub: '單元 05–06。本課程的核心：兩條路徑與 ECOS 輸入。',
      qs: [
        { q: '離子層析測出來陰陽離子不平衡，最主要的兩個原因是什麼？',
          o: ['分析誤差，以及有離子（最常見的是碳酸根）沒被測到',
              '溫度變化與濕度變化',
              '樣品汙染與儀器老化',
              '材料的孔隙結構與取樣深度'],
          a: 0,
          e: '溶液必須電中性，所以測到不平衡只能是這兩個原因。關鍵差別：分析誤差沒有方向性，而漏測碳酸根<strong>只會</strong>造成陽離子過剩。',
          r: [5, '電荷平衡與兩條路徑'] },

        { q: '哪些條件會讓 SaltsR 判定走 <strong>Pathway 1</strong>？',
          o: ['Δe ≤ 2 % × max(Σ陰, Σ陽)，<strong>或</strong> 陰離子過剩',
              '只有當 Δe ≤ 2 % 時',
              '只有當陽離子過剩時',
              'Δe &gt; 2 % 且陽離子過剩'],
          a: 0,
          e: '兩個條件是「或」的關係。陰離子過剩之所以也走 Pathway 1，是因為沒有「漏測某個陰離子」這種現成的解釋，只能歸因於分析誤差。',
          r: [5, '電荷平衡與兩條路徑'] },

        { q: 'Pathway 1 的等比例調整，做完之後每個離子彼此的相對比例會怎樣？',
          o: ['完全不變 —— 這正是「不怪罪任何特定離子」的數學表現',
              '陰離子的比例會改變，陽離子不變',
              '全部變成相等',
              '按分子量重新分配'],
          a: 0,
          e: '陰離子全體乘同一個係數、陽離子全體乘另一個係數，所以組內的比例完全保持。這與 Pathway 2「挑特定離子開刀」形成鮮明對比。',
          r: [5, '電荷平衡與兩條路徑'] },

        { q: 'Pathway 2 的扣除順序是 Ca²⁺ → Mg²⁺ → Na⁺ → K⁺。這個順序的依據是什麼？',
          o: ['對應碳酸鹽的溶解度由小到大：CaCO₃ 最難溶，最可能以固體穩定存在',
              '對應離子半徑由大到小',
              '對應分子量由大到小',
              '對應在自然界的豐度由高到低'],
          a: 0,
          e: '過剩的陽離子被假設為碳酸鹽。最難溶的碳酸鹽最可能留在牆體裡不被水帶走，所以優先扣它。這是一個有物理根據的假設，不是任意排序。',
          r: [5, '電荷平衡與兩條路徑'] },

        { q: 'MH-01 走 Pathway 2 之後，鈣被扣到 0。正確的理解是什麼？',
          o: ['模型假設這些鈣全部以難溶的 CaCO₃ 存在，不參與潮解結晶循環，所以排除在模擬之外',
              '這面牆確實沒有鈣',
              '計算出錯了，應該修正',
              '鈣被硫酸根消耗成石膏了'],
          a: 0,
          e: '這是<strong>假設，不是測量結果</strong>。如果那些鈣實際上是以極易潮解的 CaCl₂ 存在，這個假設會嚴重低估風險 —— 所以報告裡一定要註明走了哪條路徑、扣了多少。',
          r: [5, '電荷平衡與兩條路徑'] },

        { q: '式 6 把石膏上限定為 <code>min(SO₄_adj, Ca_adj)</code>。取最小值的化學意義是什麼？',
          o: ['CaSO₄ 是 1:1 化合物，先用完的那一個就是限量試劑，決定石膏能生成多少',
              '取最小值可以避免負數',
              '硫酸根總是比鈣少',
              '這是為了讓計算比較快'],
          a: 0,
          e: '限量試劑的概念。要生成 1 當量石膏需要 1 當量 Ca 加 1 當量 SO₄，誰先耗盡，石膏就停在哪裡。',
          r: [6, '石膏扣除與 ECOS 輸入'] },

        { q: '為什麼 ECOS/Runsalt 模型要把石膏排除？',
          o: ['石膏溶解度極低（20 °C 約 2.14 g/L），幾乎不潮解、不參與濕度循環，在鹽害模擬中是惰性的',
              '因為石膏對建材無害',
              '因為石膏不含在離子層析的測定範圍內',
              '因為石膏的分子量太大'],
          a: 0,
          e: '此外 ECOS 最多只處理六種離子，SO₄²⁻ 與 Ca²⁺ 不能同時完整存在（Godts et al. 2022, <em>Heritage</em>）。但要注意：<strong>石膏被排除在模擬之外，不代表它對建材無害</strong>，它仍是重要的劣化因子。',
          r: [6, '石膏扣除與 ECOS 輸入'] },

        { q: '扣除石膏時同時從 SO₄ 和 Ca 各扣掉相同的當量。這對電荷平衡有什麼影響？',
          o: ['沒有影響 —— 兩邊各扣同樣多的當量，扣完仍然中性',
              '會讓陰離子變少，需要重新平衡',
              '會讓陽離子變少，需要重新平衡',
              '會讓總電荷變成負的'],
          a: 0,
          e: '這是設計上的巧思：因為 CaSO₄ 是 1:1 而且電荷相同（各 2 價），一邊扣一個當量，平衡自然維持。',
          r: [6, '石膏扣除與 ECOS 輸入'] },

        { q: '石膏飽和度 S &gt; 1 代表什麼？正確的處理是什麼？',
          o: ['萃取水不足以溶解全部石膏，測到的 Ca 與 SO₄ 偏低；應提高稀釋倍率<strong>重新萃取</strong>',
              '樣品裡的石膏太少，應該增加樣品量',
              '只要在計算時把水量參數改大就好',
              '代表數據品質很好，可以直接使用'],
          a: 0,
          e: '演算法只能告訴你「這個數字不可信」，它沒辦法把沒溶掉的石膏變出來。在計算裡改水量參數只會改變<em>算式</em>，不會改變<em>已經測錯的 ppm</em>。',
          r: [6, '石膏扣除與 ECOS 輸入'] },

        { q: 'Runsalt 需要的輸入是什麼形式的數值？',
          o: ['莫耳分率（七個離子各自占總莫耳數的比例，加起來等於 1）',
              'ppm',
              'mEq/kg',
              '絕對莫耳數（mol）'],
          a: 0,
          e: '式 8 先把 mEq/kg 除以電荷數再除 1000 得 mol/kg，再除以總和得莫耳分率。Runsalt 也接受 weight 格式，用檔案裡的 <code>unit</code> 欄位切換。',
          r: [6, '石膏扣除與 ECOS 輸入'] }
      ]
    },

    {
      title: '階段 4 · 讀檔、繪圖與判讀',
      sub: '單元 07–09。把模擬結果變成一句可執行的建議。',
      qs: [
        { q: 'Runsalt 匯出的檔案裡，<code>NaCl_X</code> 和 <code>NaCl_Y</code> 兩列分別是什麼？',
          o: ['X 是相對濕度，Y 是該鹽以固體形式存在的莫耳量',
              'X 是溫度，Y 是濕度',
              'X 是時間，Y 是濃度',
              'X 是莫耳量，Y 是相對濕度'],
          a: 0,
          e: '每個鹽相佔兩列。不同鹽的 X 範圍長度不一樣，因為每個鹽只在自己的穩定濕度區間存在。',
          r: [7, '讀進 Runsalt 輸出檔'] },

        { q: '為什麼分析之前要把 Runsalt 的「寬格式」轉成「長格式」？',
          o: ['長格式每列代表一個觀測（一個鹽、一個濕度、一個莫耳量），畫圖、篩選、分組統計都變得直接',
              '因為寬格式檔案太大',
              '因為 R 不能讀寬格式',
              '因為長格式比較省記憶體'],
          a: 0,
          e: 'tidy 資料是資料科學的核心觀念。轉成長格式之後，「依鹽分組」「依濕度篩選」都變成一行程式。',
          r: [7, '讀進 Runsalt 輸出檔'] },

        { q: '在 RH–莫耳曲線圖上，一條曲線「結束的那一點」（最右端）代表什麼？',
          o: ['該鹽完全溶解的濕度，也就是結晶／潮解的臨界 RH',
              '該鹽含量最高的濕度',
              '模擬計算的上限',
              '該鹽開始形成的濕度'],
          a: 0,
          e: '從高濕往低濕走時，就是在這一點開始結晶。SaltsR 把它記在 <code>Crystallisation</code> 欄。',
          r: [8, '畫圖，然後看懂它'] },

        { q: '課程範例中，岩鹽（NaCl）的臨界 RH 是 69.78 %，但純 NaCl 的潮解 RH 約 75 %。這個差異說明了什麼？',
          o: ['混合系統中其他離子的存在降低了水的活性，把臨界點拉低了 —— 所以不能查單鹽表',
              '模擬結果不準確',
              '溫度不同造成的',
              '樣品裡的 NaCl 純度不夠'],
          a: 0,
          e: '這是實務上非常關鍵的一點：如果按照純鹽表把濕度控制在 72 % 以為安全，實際上這面牆在 70 % 就已經開始結晶了。',
          r: [8, '畫圖，然後看懂它'] },

        { q: '判斷「哪個鹽最危險」時，最關鍵的考量是什麼？',
          o: ['它的臨界 RH 是否落在當地環境濕度的波動範圍內，因而會反覆被跨越',
              '它的絕對含量是否最高',
              '它的分子量是否最大',
              '它是否含有硫酸根'],
          a: 0,
          e: '風險 = 鹽的性質 × 當地氣候。無水芒硝雖然惡名昭彰，但它的臨界 RH 只有 16.66 %，在台灣幾乎不會被跨越，在<em>這個</em>環境下反而不構成主要威脅。',
          r: [8, '畫圖，然後看懂它'] },

        { q: '對古蹟管理者的濕度控制建議，最核心的原則是什麼？',
          o: ['濕度的<strong>穩定性</strong>比絕對數值更重要 —— 避免反覆進出臨界值',
              '濕度越低越好',
              '濕度越高越好',
              '把濕度控制在 50 % 一定安全'],
          a: 0,
          e: '長期穩定在 65 % 的破壞，會遠小於每天在 55–75 % 之間來回。因為破壞來自<strong>循環次數</strong>，不是單次的絕對狀態。此外極低濕度會傷害木構件與彩繪層。',
          r: [8, '畫圖，然後看懂它'] },

        { q: '要對資料框的每一列跑一次 <code>fun_salt_balance()</code>，下列哪個寫法是對的？',
          o: ['<code>for (i in 1:nrow(samples)) { ... }</code> 或 <code>lapply(1:nrow(samples), function(i) ...)</code>',
              '<code>fun_salt_balance(samples)</code>',
              '<code>samples * fun_salt_balance</code>',
              '<code>apply(fun_salt_balance, samples)</code>'],
          a: 0,
          e: '<code>for</code> 比較好懂，<code>lapply</code> 比較簡潔且是 R 的慣用寫法。兩者結果相同。',
          r: [9, '批次處理與綜合實作'] },

        { q: 'Godts 等人分析 11 412 個真實樣品後歸納出兩種常見混合型態。<strong>Type 2（鈣型）</strong>的特徵是什麼？',
          o: ['以 NO₃⁻ 與 Ca²⁺ 為主，吸濕性明顯較高，牆面容易長期潮濕',
              '以 SO₄²⁻ 與 Na⁺ 為主，吸濕性較低',
              '只含氯化物',
              '不含任何陽離子'],
          a: 0,
          e: 'Type 1 是硫酸鹽型（SO₄ &gt; Na &gt; K &gt; NO₃ &gt; Cl &gt; Mg，吸濕性較低）；Type 2 是鈣型（NO₃ &gt; Ca &gt; Cl &gt; Na &gt; K &gt; Mg，吸濕性高、破壞潛勢大）。',
          r: [9, '批次處理與綜合實作'] },

        { q: '判斷樣品屬於哪一種混合型態時，應該看校正前還是校正後的離子組成？為什麼？',
          o: ['看<strong>校正前</strong>。因為 Pathway 2 常把鈣扣到 0，校正後會讓鈣型樣品看起來「不像鈣型」',
              '看校正後，因為那才是餵給模型的數字',
              '兩者都可以，結果一樣',
              '要看扣除石膏之後的莫耳分率'],
          a: 0,
          e: '這是一個很容易踩到的方法學陷阱。校正後的組成是為了<em>餵給熱力學模型</em>而準備的，不是對樣品化學組成的最佳估計。',
          r: [9, '批次處理與綜合實作'] },

        { q: 'SaltsR 輸出的 <code>total_ion_content</code> 欄位，實際上算的是什麼？',
          o: ['被校正掉的差額減去石膏，<strong>不是</strong>總離子含量；總可溶鹽應看 <code>total_wt_adj</code>',
              '樣品的總離子含量，可以直接使用',
              '扣除石膏後的莫耳分率總和',
              '陰離子與陽離子的當量總和'],
          a: 0,
          e: '以 MH-01 為例，這個欄位給 0.162 wt%，但實際可溶鹽是 1.538 wt%。<strong>教訓比欄位本身重要：拿到任何軟體的輸出，都要去確認那一欄的定義，而不是照著名稱猜。</strong>',
          r: [6, '石膏扣除與 ECOS 輸入'] },

        { q: '做完這門課，如果要進行真實的文化資產診斷，應該使用什麼工具？',
          o: ['官方工具與最新演算法（PREDICT 鹽含量計算器、Runsalt），本課程的目的是讓你看懂它們在做什麼',
              '就用這個課程網站的計算器',
              '用 Excel 自己重寫一次',
              '直接把 ppm 交給客戶判斷'],
          a: 0,
          e: 'SaltsR 作者本人在套件說明中就指出，最新的計算請以 PREDICT 計算器為準。理解原理 ≠ 取代專業工具 —— 但理解原理讓你能<strong>判斷工具的輸出合不合理</strong>，這才是這門課真正的價值。',
          r: [6, '石膏扣除與 ECOS 輸入'] }
      ]
    }
  ];

  const TOTAL = STAGES.reduce((s, st) => s + st.qs.length, 0);
  const PASS = 70;
  let answered = 0, correct = 0;
  const stageScore = STAGES.map(() => ({ ok: 0, n: 0 }));

  /** 以題號為種子的確定性輪轉，避免正確答案總是落在第一個選項 */
  function rotate(n, seed) {
    const shift = (seed * 3 + Math.floor(seed / 4)) % n;
    return Array.from({ length: n }, (_, i) => (i + shift) % n);
  }

  function build() {
    const root = document.getElementById('quiz-root');
    if (!root) return;
    let qi = 0;
    STAGES.forEach((st, si) => {
      stageScore[si].n = st.qs.length;
      const sec = document.createElement('section');
      sec.className = 'stage';
      sec.id = 'stage' + (si + 1);
      sec.innerHTML = `<div class="stage-head"><h3>${st.title}</h3><div class="sm">${st.sub}　共 ${st.qs.length} 題</div></div>`;
      st.qs.forEach((q) => {
        qi++;
        // 固定但非「答案永遠在第一個」的選項排序：
        // 以題號為種子做確定性輪轉，讓每次開啟看到的順序一致（方便對答案），
        // 但正確選項會分散在四個位置上。
        const order = rotate(q.o.length, qi);
        const shown = order.map((k) => q.o[k]);
        const ansPos = order.indexOf(q.a);

        const d = document.createElement('div');
        d.className = 'q';
        d.innerHTML =
          `<div class="qn">Q${String(qi).padStart(2, '0')} / ${TOTAL}</div>
           <div class="qt">${q.q}</div>
           <div class="opts">${shown.map((o, oi) =>
             `<label class="opt"><input type="radio" name="q${qi}" value="${oi}"><span>${o}</span></label>`).join('')}</div>
           <div class="fb"></div>`;
        d.dataset.ans = 'ABCD'[ansPos];
        const fb = d.querySelector('.fb');
        const opts = [...d.querySelectorAll('.opt')];
        opts.forEach((lab, oi) => {
          lab.querySelector('input').addEventListener('change', () => {
            if (d.dataset.done) return;
            d.dataset.done = '1';
            const ok = oi === ansPos;
            answered++; if (ok) { correct++; stageScore[si].ok++; }
            opts.forEach((l2, o2) => {
              l2.classList.add('disabled');
              l2.querySelector('input').disabled = true;
              if (o2 === ansPos) l2.classList.add('correct');
              else if (o2 === oi) l2.classList.add('wrong');
            });
            fb.className = 'fb show ' + (ok ? 'ok' : 'no');
            fb.innerHTML = (ok ? '<strong>✓ 答對了。</strong> ' : '<strong>✗ 再想一下。</strong> ') +
              q.e + `<br><span class="small">複習：${L(q.r[0], q.r[1])}</span>`;
            update();
          });
        });
        sec.appendChild(d);
      });
      root.appendChild(sec);
    });
  }

  function update() {
    const pct = answered ? Math.round(100 * correct / answered) : 0;
    const done = Math.round(100 * answered / TOTAL);
    document.getElementById('sc-correct').textContent = correct + ' / ' + answered;
    document.getElementById('sc-pct').textContent = pct + '%';
    document.getElementById('sc-prog').style.width = done + '%';
    document.getElementById('sc-left').textContent = (TOTAL - answered) + ' 題未作答';

    const bars = document.getElementById('stagebars');
    if (bars) {
      bars.innerHTML = STAGES.map((st, i) => {
        const s = stageScore[i], p = s.n ? Math.round(100 * s.ok / s.n) : 0;
        return `<div class="sb"><div class="n">${st.title.split('·')[1].trim()}</div>
          <div class="tiny muted">${s.ok} / ${s.n} 題正確</div>
          <div class="bar"><i style="width:${p}%;background:${p >= 70 ? 'var(--teal)' : (p >= 40 ? 'var(--gold)' : 'var(--coral)')}"></i></div></div>`;
      }).join('');
    }

    const res = document.getElementById('result');
    if (answered === TOTAL) {
      const finalPct = Math.round(100 * correct / TOTAL);
      const weak = STAGES.map((st, i) => ({ st, i, p: stageScore[i].ok / stageScore[i].n }))
        .filter((x) => x.p < 0.7);
      res.style.display = '';
      res.className = 'callout ' + (finalPct >= PASS ? '' : 'warn');
      res.innerHTML = `<span class="ct">${finalPct >= PASS ? '🎉 通過！' : '再加油一點'}</span>
        <p>你答對 <strong>${correct} / ${TOTAL}</strong> 題，得分 <strong>${finalPct} 分</strong>
        （通過門檻 ${PASS} 分）。</p>` +
        (weak.length
          ? `<p style="margin-bottom:0">建議優先複習這些階段：<br>${weak.map((w) =>
              `· <strong>${w.st.title}</strong> —— ${w.st.sub}`).join('<br>')}</p>`
          : `<p style="margin-bottom:0">四個階段都達到 70 % 以上。
             下一步：到<a href="lesson.html#u9">單元 09</a> 完成綜合實作，
             把八個樣品寫成一份完整的牆體診斷報告。</p>`);
      res.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function init() {
    build(); update();
    const rb = document.getElementById('restart');
    if (rb) rb.addEventListener('click', () => location.reload());
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
