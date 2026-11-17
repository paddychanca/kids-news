(function () {
  var data = JSON.parse(document.getElementById("edition-data").textContent);
  var names = Object.keys(data);
  var tabsEl = document.getElementById("tabs");
  var storiesEl = document.getElementById("stories");
  var langBtn = document.getElementById("lang-toggle");
  var footerNote = document.getElementById("footer-note");

  var lang = "en";
  var currentTab = null;

  var UI = {
    en: {
      from: "From ",
      simple: "Simpler please",
      normal: "Back to normal",
      read: "\uD83D\uDD0A Read to me",
      original: "Read the original story",
      why: "Why it matters: ",
      quiz: "Quick quiz: ",
      correct: "Correct! ",
      wrong: "Not quite. ",
      empty: "No stories here today.",
      toggle: "Fran\u00e7ais",
      nosound: "Reading aloud is not available",
      footer: "These stories are rewritten by AI for young readers. Tap \"Read the original story\" to see what the news organization published."
    },
    fr: {
      from: "Source : ",
      simple: "Plus simple, s'il te pla\u00eet",
      normal: "Retour \u00e0 la version normale",
      read: "\uD83D\uDD0A Lis-moi l'article",
      original: "Lire l'article original",
      why: "Pourquoi c'est important : ",
      quiz: "Petit quiz : ",
      correct: "Bravo ! ",
      wrong: "Pas tout \u00e0 fait. ",
      empty: "Aucun article ici aujourd'hui.",
      toggle: "English",
      nosound: "La lecture \u00e0 voix haute n'est pas disponible",
      footer: "Ces articles sont r\u00e9\u00e9crits par une IA pour les jeunes lecteurs. Appuie sur \u00ab Lire l'article original \u00bb pour voir ce que le m\u00e9dia a publi\u00e9."
    }
  };

  var TAB_NAMES_FR = {
    "World": "Monde",
    "Space": "Espace",
    "Animals": "Animaux",
    "Science": "Sciences",
    "Earth & disasters": "Terre et catastrophes",
    "Tech and AI": "Techno et IA",
    "Health": "Sant\u00e9"
  };

  function t(key) { return UI[lang][key]; }

  function tabLabel(name) {
    if (lang === "fr" && TAB_NAMES_FR[name]) return TAB_NAMES_FR[name];
    return name;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function stopSpeaking() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  var LETTER = /[\p{L}\p{N}]/u;

  function renderText(container, text, hardWords, defBox) {
    container.textContent = "";
    var words = (hardWords || []).filter(function (w) { return w && w.word; });
    if (!words.length) {
      container.textContent = text;
      return;
    }
    var pattern = new RegExp(
      "(" + words.map(function (w) { return escapeRegExp(w.word); }).join("|") + ")",
      "giu"
    );
    var last = 0;
    var m;
    while ((m = pattern.exec(text)) !== null) {
      var before = m.index > 0 ? text.charAt(m.index - 1) : "";
      var after = text.charAt(m.index + m[0].length);
      if (LETTER.test(before) || LETTER.test(after)) continue;
      if (m.index > last) {
        container.appendChild(document.createTextNode(text.slice(last, m.index)));
      }
      var hit = m[0].toLowerCase();
      var found = words.filter(function (w) { return w.word.toLowerCase() === hit; })[0];
      var b = el("button", "hard", m[0]);
      b.type = "button";
      (function (f) {
        b.addEventListener("click", function () {
          defBox.textContent = f.word + " : " + f.meaning;
          defBox.hidden = false;
        });
      })(found);
      container.appendChild(b);
      last = m.index + m[0].length;
    }
    if (last < text.length) {
      container.appendChild(document.createTextNode(text.slice(last)));
    }
  }

  var voices = [];
  function loadVoices() {
    if ("speechSynthesis" in window) voices = window.speechSynthesis.getVoices();
  }
  loadVoices();
  if ("speechSynthesis" in window) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  function pickVoice(code) {
    var prefs = code === "fr" ? ["fr-ca", "fr-fr"] : ["en-ca", "en-us", "en-gb"];
    var list = voices.map(function (v) {
      return { v: v, l: v.lang.toLowerCase().replace("_", "-") };
    });
    for (var i = 0; i < prefs.length; i++) {
      for (var j = 0; j < list.length; j++) {
        if (list[j].l === prefs[i]) return list[j].v;
      }
    }
    for (var k = 0; k < list.length; k++) {
      if (list[k].l.indexOf(code) === 0) return list[k].v;
    }
    return null;
  }

  function makeReadButton(getSpeech) {
    var btn = el("button", "btn", t("read"));
    btn.type = "button";
    btn.addEventListener("click", function () {
      if (!("speechSynthesis" in window)) {
        btn.textContent = t("nosound");
        return;
      }
      if (btn.classList.contains("on")) {
        window.speechSynthesis.cancel();
        btn.classList.remove("on");
        return;
      }
      window.speechSynthesis.cancel();
      var speech = getSpeech();
      setTimeout(function () {
        var u = new SpeechSynthesisUtterance(speech.text);
        var v = pickVoice(speech.code);
        if (v) {
          u.voice = v;
          u.lang = v.lang;
        } else {
          u.lang = speech.code === "fr" ? "fr-CA" : "en-US";
        }
        u.rate = 0.95;
        u.onend = u.onerror = function () { btn.classList.remove("on"); };
        btn.classList.add("on");
        window.speechSynthesis.speak(u);
      }, 100);
    });
    return btn;
  }
  function content(s) {
    if (lang === "fr" && s.fr && s.fr.summary) return s.fr;
    return s;
  }

  function speechCode(s) {
    return (lang === "fr" && s.fr && s.fr.summary) ? "fr" : "en";
  }

  function buildQuiz(q) {
    if (!q || !q.question || !q.options || q.options.length < 2) return null;
    var box = el("div", "quiz");
    box.appendChild(el("p", "q", t("quiz") + q.question));
    var feedback = el("p", "feedback");
    var buttons = [];
    q.options.forEach(function (opt, i) {
      var b = el("button", "option", opt);
      b.type = "button";
      b.addEventListener("click", function () {
        buttons.forEach(function (x) { x.disabled = true; });
        if (i === q.answer_index) {
          b.classList.add("correct");
          feedback.textContent = t("correct") + (q.explanation || "");
        } else {
          b.classList.add("wrong");
          if (buttons[q.answer_index]) buttons[q.answer_index].classList.add("correct");
          feedback.textContent = t("wrong") + (q.explanation || "");
        }
      });
      buttons.push(b);
      box.appendChild(b);
    });
    box.appendChild(feedback);
    return box;
  }

  function buildCard(s) {
    var c = content(s);
    var card = el("article", "card");
    card.appendChild(el("p", "source-line", t("from") + (s.source || "")));
    card.appendChild(el("h2", null, c.headline || s.headline));

    var summary = el("p", "summary");
    var defBox = el("p", "definition");
    defBox.hidden = true;
    var simple = false;

    function showText() {
      var text = simple ? (c.simple || c.summary) : c.summary;
      renderText(summary, text, c.hard_words, defBox);
      defBox.hidden = true;
    }
    showText();
    card.appendChild(summary);
    card.appendChild(defBox);

    if (c.why_it_matters) {
      card.appendChild(el("p", "why", t("why") + c.why_it_matters));
    }

    var buttons = el("div", "buttons");

    var simpleBtn = el("button", "btn", t("simple"));
    simpleBtn.type = "button";
    simpleBtn.addEventListener("click", function () {
      simple = !simple;
      simpleBtn.classList.toggle("on", simple);
      simpleBtn.textContent = simple ? t("normal") : t("simple");
      showText();
    });
    if (c.simple) buttons.appendChild(simpleBtn);

    buttons.appendChild(makeReadButton(function () {
      return {
        text: (c.headline || s.headline) + ". " + (simple ? (c.simple || c.summary) : c.summary),
        code: speechCode(s)
      };
    }));

    if (s.link) {
      var a = el("a", "btn", t("original"));
      a.href = s.link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      buttons.appendChild(a);
    }
    card.appendChild(buttons);

    var quiz = buildQuiz(c.quiz);
    if (quiz) card.appendChild(quiz);

    return card;
  }
  function buildTabs() {
    tabsEl.textContent = "";
    names.forEach(function (name) {
      var tab = el("button", "tab", tabLabel(name));
      tab.type = "button";
      tab.dataset.name = name;
      tab.addEventListener("click", function () { selectTab(name); });
      tabsEl.appendChild(tab);
    });
  }

  function selectTab(name, keepScroll) {
    stopSpeaking();
    currentTab = name;
    Array.prototype.forEach.call(tabsEl.children, function (tab) {
      tab.classList.toggle("active", tab.dataset.name === name);
    });
    storiesEl.textContent = "";
    var list = data[name] || [];
    if (!list.length) {
      storiesEl.appendChild(el("p", "empty", t("empty")));
    }
    list.forEach(function (s) { storiesEl.appendChild(buildCard(s)); });
    try { localStorage.setItem("kidsnews-tab", name); } catch (e) {}
    if (!keepScroll) window.scrollTo(0, 0);
  }

  function applyLanguage() {
    document.documentElement.lang = lang;
    langBtn.textContent = t("toggle");
    if (footerNote) footerNote.textContent = t("footer");
    buildTabs();
    selectTab(currentTab, true);
  }

  if (!names.length) {
    storiesEl.appendChild(el("p", "empty", "No stories today. Please check back tomorrow."));
    return;
  }

  langBtn.addEventListener("click", function () {
    lang = lang === "en" ? "fr" : "en";
    try { localStorage.setItem("kidsnews-lang", lang); } catch (e) {}
    applyLanguage();
  });

  currentTab = names[0];
  try {
    var savedTab = localStorage.getItem("kidsnews-tab");
    if (savedTab && names.indexOf(savedTab) !== -1) currentTab = savedTab;
    var savedLang = localStorage.getItem("kidsnews-lang");
    if (savedLang === "fr" || savedLang === "en") lang = savedLang;
  } catch (e) {}

  applyLanguage();
})();