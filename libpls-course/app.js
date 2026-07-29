/* libPLS 課程閱讀器：章節切換、進度、程式碼複製、測驗與響應式導覽 */
(function () {
  "use strict";

  const course = window.LIBPLS_COURSE;
  if (!course || !Array.isArray(course.lessons)) return;

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const storageKey = "libpls-course-state-v1";

  const defaultState = {
    current: 1,
    completed: [],
    theme: "light",
    fontScale: 1,
    quizAnswers: {}
  };

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      return {
        ...defaultState,
        ...saved,
        completed: Array.isArray(saved?.completed) ? saved.completed : []
      };
    } catch (_) {
      return { ...defaultState };
    }
  }

  let state = loadState();

  function saveState() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (_) {
      /* file:// 或隱私模式若禁用儲存，課程仍可使用。 */
    }
  }

  function lessonFromHash() {
    const match = location.hash.match(/^#lesson-(\d+)$/);
    const id = match ? Number(match[1]) : state.current;
    return course.lessons.some(x => x.id === id) ? id : 1;
  }

  function slug(text, index) {
    return `section-${state.current}-${index + 1}`;
  }

  function renderCurriculum() {
    const list = $("#lesson-list");
    list.innerHTML = course.lessons.map(lesson => {
      const active = lesson.id === state.current;
      const completed = state.completed.includes(lesson.id);
      return `
        <li class="lesson-item ${active ? "active" : ""} ${completed ? "completed" : ""}">
          <button class="lesson-link" type="button" data-lesson="${lesson.id}"
                  ${active ? 'aria-current="page"' : ""}>
            <span class="lesson-number">${completed ? "✓" : lesson.id}</span>
            <span>
              <span class="lesson-name">第 ${lesson.id} 章｜${lesson.shortTitle}</span>
              <span class="lesson-duration">${lesson.level} · ${lesson.duration}</span>
            </span>
            <span class="lesson-state">${completed ? "✓" : ""}</span>
          </button>
        </li>`;
    }).join("");

    $$(".lesson-link", list).forEach(button => {
      button.addEventListener("click", () => navigate(Number(button.dataset.lesson)));
    });
  }

  function quizHTML(quiz) {
    if (!quiz) return "";
    const saved = state.quizAnswers[state.current];
    return `
      <section class="checkpoint" id="checkpoint">
        <h3>章末檢核</h3>
        <p><strong>${quiz.question}</strong></p>
        <div class="checkpoint-options">
          ${quiz.options.map((option, index) => `
            <label class="checkpoint-option">
              <input type="radio" name="quiz-${state.current}" value="${index}"
                     ${Number(saved) === index ? "checked" : ""}>
              <span>${option}</span>
            </label>`).join("")}
        </div>
        <button class="check-answer" type="button">檢查答案</button>
        <div class="quiz-feedback" role="status"></div>
      </section>`;
  }

  function renderLesson() {
    const lesson = course.lessons.find(x => x.id === state.current);
    document.title = `${lesson.title}｜${course.title}`;
    $("#lesson-kicker").textContent = `第 ${lesson.id} 章｜${lesson.level}`;
    $("#lesson-position").textContent = `${lesson.id} / ${course.lessons.length}`;
    $("#lesson-title").textContent = lesson.title;
    $("#lesson-level").textContent = `${lesson.level}課程 · ${lesson.duration}`;
    $("#objective-text").textContent = lesson.objective;

    $("#lesson-body").innerHTML = lesson.sections.map((section, index) => `
      <section id="${slug(section.title, index)}">
        <h2>${section.title}</h2>
        ${section.body}
      </section>`).join("") + quizHTML(lesson.quiz);

    renderOutline(lesson);
    renderKeyPoints(lesson);
    bindCodeCopy();
    bindQuiz(lesson);
    updateCompleteButton();
    updatePagination();
  }

  function renderOutline(lesson) {
    $("#outline-list").innerHTML = lesson.sections.map((section, index) => `
      <li><a href="#${slug(section.title, index)}">${section.title}</a></li>
    `).join("");
  }

  function renderKeyPoints(lesson) {
    $("#key-point-list").innerHTML = lesson.keyPoints
      .map(point => `<li>${point}</li>`).join("");
  }

  function bindCodeCopy() {
    $$(".copy-button").forEach(button => {
      button.addEventListener("click", async () => {
        const codeText = button.closest(".code-block").querySelector("code").textContent;
        const label = $("span", button);
        try {
          await navigator.clipboard.writeText(codeText);
        } catch (_) {
          const area = document.createElement("textarea");
          area.value = codeText;
          area.style.position = "fixed";
          area.style.opacity = "0";
          document.body.append(area);
          area.select();
          document.execCommand("copy");
          area.remove();
        }
        button.classList.add("copied");
        label.textContent = "已複製";
        window.setTimeout(() => {
          button.classList.remove("copied");
          label.textContent = "複製";
        }, 1500);
      });
    });
  }

  function bindQuiz(lesson) {
    const checkButton = $(".check-answer");
    if (!checkButton || !lesson.quiz) return;

    checkButton.addEventListener("click", () => {
      const chosen = $(`input[name="quiz-${lesson.id}"]:checked`);
      const feedback = $(".quiz-feedback");
      if (!chosen) {
        feedback.textContent = "請先選擇一個答案。";
        feedback.className = "quiz-feedback visible wrong";
        return;
      }
      const value = Number(chosen.value);
      state.quizAnswers[lesson.id] = value;
      saveState();
      const correct = value === lesson.quiz.answer;
      feedback.textContent = correct
        ? lesson.quiz.explanation
        : `再想一下。${lesson.quiz.explanation}`;
      feedback.className = `quiz-feedback visible${correct ? "" : " wrong"}`;
    });
  }

  function updateCompleteButton() {
    const button = $("#complete-button");
    const completed = state.completed.includes(state.current);
    button.classList.toggle("completed", completed);
    $("span", button).textContent = completed ? "已完成本章" : "標記完成";
    button.setAttribute("aria-pressed", String(completed));
  }

  function updatePagination() {
    const prev = $("#prev-lesson");
    const next = $("#next-lesson");
    prev.disabled = state.current === 1;
    next.disabled = state.current === course.lessons.length;

    const prevLesson = course.lessons[state.current - 2];
    const nextLesson = course.lessons[state.current];
    $("span", prev).textContent = prevLesson
      ? `上一章：${prevLesson.shortTitle}` : "上一章";
    $("span", next).textContent = nextLesson
      ? `下一章：${nextLesson.shortTitle}` : "課程完成";
  }

  function updateProgress() {
    const count = state.completed.length;
    const total = course.lessons.length;
    const percent = Math.round(count / total * 100);
    $("#progress-percent").textContent = `${percent}%`;
    $("#progress-bar").style.width = `${percent}%`;
    $("#chapter-progress-label").textContent = `${count} / ${total}`;
    $("#chapter-progress-bar").style.width = `${percent}%`;
  }

  function navigate(id, replace = false) {
    const valid = Math.max(1, Math.min(course.lessons.length, id));
    state.current = valid;
    saveState();
    const hash = `#lesson-${valid}`;
    if (replace) history.replaceState(null, "", hash);
    else if (location.hash !== hash) history.pushState(null, "", hash);
    render();
    closeDrawer();
    $("#lesson").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function render() {
    state.current = lessonFromHash();
    renderCurriculum();
    renderLesson();
    updateProgress();
  }

  function toggleComplete() {
    if (state.completed.includes(state.current)) {
      state.completed = state.completed.filter(id => id !== state.current);
    } else {
      state.completed = [...state.completed, state.current].sort((a, b) => a - b);
    }
    saveState();
    renderCurriculum();
    updateCompleteButton();
    updateProgress();
  }

  function applyTheme() {
    document.documentElement.dataset.theme = state.theme;
    $("#theme-toggle").setAttribute(
      "aria-label",
      state.theme === "dark" ? "切換淺色模式" : "切換深色模式"
    );
  }

  function applyFontScale() {
    state.fontScale = Math.max(.88, Math.min(1.22, Number(state.fontScale) || 1));
    document.documentElement.style.setProperty("--reader-scale", state.fontScale);
  }

  function openDrawer() {
    $("#curriculum").classList.add("open");
    $("#drawer-scrim").hidden = false;
    $("#menu-toggle").setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    $("#curriculum").classList.remove("open");
    $("#drawer-scrim").hidden = true;
    $("#menu-toggle").setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  $("#complete-button").addEventListener("click", toggleComplete);
  $("#start-button").addEventListener("click", () => {
    const first = $(".lesson-body section");
    if (first) first.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  $("#prev-lesson").addEventListener("click", () => navigate(state.current - 1));
  $("#next-lesson").addEventListener("click", () => navigate(state.current + 1));

  $("#theme-toggle").addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    applyTheme();
    saveState();
  });

  $("#font-smaller").addEventListener("click", () => {
    state.fontScale -= .06;
    applyFontScale();
    saveState();
  });
  $("#font-larger").addEventListener("click", () => {
    state.fontScale += .06;
    applyFontScale();
    saveState();
  });
  $("#font-reset").addEventListener("click", () => {
    state.fontScale = 1;
    applyFontScale();
    saveState();
  });

  $("#menu-toggle").addEventListener("click", openDrawer);
  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#drawer-scrim").addEventListener("click", closeDrawer);

  $$(".course-categories button").forEach(button => {
    button.addEventListener("click", () => navigate(Number(button.dataset.jump)));
  });

  window.addEventListener("popstate", render);
  window.addEventListener("hashchange", () => {
    if (/^#lesson-\d+$/.test(location.hash)) render();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeDrawer();
    if (event.altKey && event.key === "ArrowLeft" && state.current > 1) {
      navigate(state.current - 1);
    }
    if (event.altKey && event.key === "ArrowRight"
        && state.current < course.lessons.length) {
      navigate(state.current + 1);
    }
  });

  applyTheme();
  applyFontScale();
  navigate(lessonFromHash(), true);
})();

