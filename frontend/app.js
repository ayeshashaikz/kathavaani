/**
 * KathaVaani (कथावाणी) — Frontend Client Application
 * Connects 6 screens from PRD.md Section 5 to the FastAPI backend.
 * Features:
 * - Dynamic /voices fetching & language/narrator capability validation
 * - Page scope slider capped at maximum 5 pages
 * - Dynamic voice preview using cached TTS endpoint
 * - Sequential synthesis with progress updates
 * - Vinyl player with text reader & MP3 download
 */

document.addEventListener('DOMContentLoaded', () => {

  // --- App State ---
  const state = {
    currentStep: 1,
    manuscript: null,        // { filename, total_pages, is_scanned, pages: [...] }
    startPage: 1,
    endPage: 1,
    selectedLanguage: 'en-IN',
    selectedNarrator: 'narrator_female', // 'narrator_female' | 'narrator_male'
    playbackSpeed: 1.0,
    voicesData: null,        // Loaded dynamically from GET /voices
    currentAudiobook: null,  // { audioId, downloadUrl, duration, text }
    sessionShelf: []         // History of audiobooks bound this session
  };

  // --- DOM Elements ---
  const screens = {
    1: document.getElementById('screen-1'),
    2: document.getElementById('screen-2'),
    3: document.getElementById('screen-3'),
    4: document.getElementById('screen-4'),
    5: document.getElementById('screen-5'),
    6: document.getElementById('screen-6'),
  };

  const stepperPips = document.querySelectorAll('.step-pip');
  const btnEnterShop = document.getElementById('btn-enter-shop');
  const btnProceedNook = document.getElementById('btn-proceed-nook');
  const btnProceedNarrator = document.getElementById('btn-proceed-narrator');
  const btnBindBook = document.getElementById('btn-bind-book');
  const btnNewBook = document.getElementById('btn-new-book');

  // Screen 2: Counter
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const samplesGrid = document.getElementById('samplesGrid');
  const manuscriptDocket = document.getElementById('manuscriptDocket');
  const docketTitle = document.getElementById('docketTitle');
  const docketFormat = document.getElementById('docketFormat');
  const docketPages = document.getElementById('docketPages');
  const docketWords = document.getElementById('docketWords');
  const docketLayer = document.getElementById('docketLayer');
  const docketSnippet = document.getElementById('docketSnippet');

  // Screen 3: Reading Nook
  const startPageSlider = document.getElementById('startPageSlider');
  const endPageSlider = document.getElementById('endPageSlider');
  const lblStartPage = document.getElementById('lblStartPage');
  const lblEndPage = document.getElementById('lblEndPage');
  const scopePageCount = document.getElementById('scopePageCount');
  const scopeWordCount = document.getElementById('scopeWordCount');
  const spineShelf = document.getElementById('spineShelf');
  const selectedLangName = document.getElementById('selectedLangName');
  const selectedLangScript = document.getElementById('selectedLangScript');

  // Screen 4: Narrator Choice
  const cardFemale = document.getElementById('card-narrator_female');
  const cardMale = document.getElementById('card-narrator_male');
  const noteFemale = document.getElementById('note-narrator_female');
  const noteMale = document.getElementById('note-narrator_male');
  const speedPills = document.querySelectorAll('.speed-pill');

  // Screen 5: Binding
  const progressFill = document.getElementById('progressFill');
  const bindingStatus = document.getElementById('bindingStatus');

  // Screen 6: Library Player
  const mainAudio = document.getElementById('mainAudio');
  const turntableVinyl = document.getElementById('turntableVinyl');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const playIcon = document.getElementById('playIcon');
  const seekSlider = document.getElementById('seekSlider');
  const currentTimeLabel = document.getElementById('currentTime');
  const totalDurationLabel = document.getElementById('totalDuration');
  const btnBack10 = document.getElementById('btnBack10');
  const btnFwd10 = document.getElementById('btnFwd10');
  const btnDownload = document.getElementById('btnDownload');
  const playerBookTitle = document.getElementById('playerBookTitle');
  const playerVoiceBadge = document.getElementById('playerVoiceBadge');
  const readerText = document.getElementById('readerText');
  const readerLangBadge = document.getElementById('readerLangBadge');
  const sessionShelfContainer = document.getElementById('sessionShelf');

  // Single audio instance for voice preview
  const previewAudio = new Audio();

  // --- Step Navigation ---
  function goToStep(step) {
    if (step < 1 || step > 6 || step === state.currentStep) return;

    const currentScreen = screens[state.currentStep];
    const nextScreen = screens[step];

    currentScreen.classList.remove('active');
    nextScreen.classList.add('active');

    state.currentStep = step;
    updateStepperUI(step);

    document.querySelector('.book-frame')
      .scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function updateStepperUI(activeStep) {
    stepperPips.forEach(pip => {
      const step = parseInt(pip.getAttribute('data-step'), 10);
      if (step === activeStep) {
        pip.classList.add('active');
      } else {
        pip.classList.remove('active');
      }
    });
  }

  document.querySelectorAll('[data-goto]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetStep = parseInt(btn.getAttribute('data-goto'), 10);
      goToStep(targetStep);
    });
  });

  // Entrance Proceed
  btnEnterShop.addEventListener('click', () => goToStep(2));

  // --- Fetch Voices from Backend (GET /voices) ---
  async function fetchVoicesConfig() {
    try {
      // Support both /voices and /api/voices
      let resp = await fetch('/voices');
      if (!resp.ok) resp = await fetch('/api/voices');
      if (!resp.ok) throw new Error("Could not load voices configuration");

      state.voicesData = await resp.json();
      buildSpineShelf();
      validateNarratorAvailability();
    } catch (err) {
      console.warn("Failed to fetch /voices:", err);
      buildSpineShelfFallback();
    }
  }

  // --- Screen 2: Counter & Upload ---
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    docketTitle.textContent = "Extracting text from " + file.name + "...";
    docketSnippet.textContent = "Extracting per-page text layer using PyMuPDF...";
    manuscriptDocket.classList.remove('hidden');
    btnProceedNook.disabled = true;

    try {
      const resp = await fetch('/api/extract', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Extraction failed');
      }

      const data = await resp.json();
      populateManuscriptDocket(data);

    } catch (err) {
      alert("Extraction Error: " + err.message);
      docketTitle.textContent = "Error loading manuscript";
      docketSnippet.textContent = err.message;
    }
  }

  function populateManuscriptDocket(data) {
    state.manuscript = data;

    docketTitle.textContent = data.filename;
    docketFormat.textContent = data.file_type.toUpperCase();
    docketPages.textContent = data.total_pages;

    const totalWords = data.pages.reduce((acc, p) => acc + (p.word_count || 0), 0);
    docketWords.textContent = totalWords.toLocaleString();

    if (data.is_scanned) {
      docketLayer.textContent = "Scanned (No Text)";
      docketLayer.className = "stat-value";
      docketLayer.style.color = "#a83226";
      docketSnippet.textContent = data.message;
      btnProceedNook.disabled = true;
      return;
    }

    docketLayer.textContent = "Selectable Text";
    docketLayer.className = "stat-value text-success";

    const preview = data.pages[0]?.text?.substring(0, 220) || "No preview available.";
    docketSnippet.textContent = `"${preview}..."`;

    // Initialize page slider with capped maximum of 5 pages
    initPageScopeSliders(data.total_pages, data.pages);

    btnProceedNook.disabled = false;
    manuscriptDocket.classList.remove('hidden');
  }

  // Sample books shelf on Screen 2
  async function loadSampleBooks() {
    try {
      const resp = await fetch('/api/samples');
      if (!resp.ok) return;
      const samples = await resp.json();

      samplesGrid.innerHTML = '';
      samples.forEach(sample => {
        const card = document.createElement('div');
        card.className = 'sample-book-card';
        card.innerHTML = `
          <span class="sample-book-lang">${sample.language_name}</span>
          <h4 class="sample-book-title">${sample.title}</h4>
          <span class="sample-book-author">${sample.author}</span>
        `;
        card.addEventListener('click', () => loadSampleContent(sample.id, sample.default_language));
        samplesGrid.appendChild(card);
      });
    } catch (err) {
      console.warn("Could not load sample books:", err);
    }
  }

  async function loadSampleContent(sampleId, defaultLang) {
    try {
      docketTitle.textContent = "Plucking volume from shelf...";
      manuscriptDocket.classList.remove('hidden');

      const resp = await fetch(`/api/samples/${sampleId}`);
      if (!resp.ok) throw new Error("Failed to load sample book");
      const data = await resp.json();

      populateManuscriptDocket(data);

      if (defaultLang) {
        selectLanguage(defaultLang);
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
  }

  btnProceedNook.addEventListener('click', () => goToStep(3));

  // --- Screen 3: Reading Nook (Page Slider max 5 & Language Picker) ---
  function initPageScopeSliders(totalPages, pages) {
    // Strictly capped at maximum 5 pages to preserve credits
    const maxAllowed = Math.min(5, Math.max(1, totalPages));

    startPageSlider.min = 1;
    startPageSlider.max = maxAllowed;
    startPageSlider.value = 1;

    endPageSlider.min = 1;
    endPageSlider.max = maxAllowed;
    endPageSlider.value = Math.min(maxAllowed, 1);

    updateScopeDisplay(pages);

    startPageSlider.oninput = () => {
      if (parseInt(startPageSlider.value, 10) > parseInt(endPageSlider.value, 10)) {
        endPageSlider.value = startPageSlider.value;
      }
      updateScopeDisplay(pages);
    };

    endPageSlider.oninput = () => {
      if (parseInt(endPageSlider.value, 10) < parseInt(startPageSlider.value, 10)) {
        startPageSlider.value = endPageSlider.value;
      }
      updateScopeDisplay(pages);
    };
  }

  function updateScopeDisplay(pages) {
    const s = parseInt(startPageSlider.value, 10);
    const e = parseInt(endPageSlider.value, 10);

    state.startPage = s;
    state.endPage = e;

    lblStartPage.textContent = `Page ${s}`;
    lblEndPage.textContent = `Page ${e}`;

    const count = (e - s + 1);
    scopePageCount.textContent = `${count} page${count > 1 ? 's' : ''} (max 5)`;

    let words = 0;
    if (pages && pages.length) {
      for (let i = s - 1; i < e && i < pages.length; i++) {
        words += (pages[i]?.word_count || 0);
      }
    }
    scopeWordCount.textContent = `~${words.toLocaleString()} words`;
  }

  // Build Spine Shelf from /voices
  function buildSpineShelf() {
    spineShelf.innerHTML = '';
    const langs = state.voicesData?.languages || {};

    Object.keys(langs).forEach(code => {
      const lang = langs[code];
      const spine = document.createElement('div');
      spine.className = `book-spine ${code === state.selectedLanguage ? 'selected' : ''}`;
      spine.setAttribute('data-lang', code);

      spine.innerHTML = `
        <div class="book-spine-gold-line"></div>
        <span class="book-spine-title">${lang.name.split(' ')[0]}</span>
        <span class="book-spine-code">${code.split('-')[0]}</span>
      `;

      spine.addEventListener('click', () => selectLanguage(code));
      spineShelf.appendChild(spine);
    });

    selectLanguage(state.selectedLanguage);
  }

  function buildSpineShelfFallback() {
    const fallbackLangs = [
      { code: 'en-IN', name: 'English', script: 'Latin' },
      { code: 'hi-IN', name: 'Hindi', script: 'Devanagari' },
      { code: 'te-IN', name: 'Telugu', script: 'Telugu' }
    ];
    spineShelf.innerHTML = '';
    fallbackLangs.forEach(lang => {
      const spine = document.createElement('div');
      spine.className = `book-spine ${lang.code === state.selectedLanguage ? 'selected' : ''}`;
      spine.setAttribute('data-lang', lang.code);
      spine.innerHTML = `<span class="book-spine-title">${lang.name}</span>`;
      spine.addEventListener('click', () => selectLanguage(lang.code));
      spineShelf.appendChild(spine);
    });
  }

  function selectLanguage(code) {
    state.selectedLanguage = code;
    const langInfo = state.voicesData?.languages?.[code] || { name: code, script: '' };

    selectedLangName.textContent = langInfo.name || code;
    selectedLangScript.textContent = langInfo.script || '';

    document.querySelectorAll('.book-spine').forEach(spine => {
      if (spine.getAttribute('data-lang') === code) {
        spine.classList.add('selected');
      } else {
        spine.classList.remove('selected');
      }
    });

    // Check narrator availability whenever language changes
    validateNarratorAvailability();
  }

  // Validate narrator availability per language using /voices mappings
  function validateNarratorAvailability() {
    if (!state.voicesData?.mappings) return;

    const langMappings = state.voicesData.mappings[state.selectedLanguage] || {};

    const checkNarrator = (narratorId, cardEl, noteEl) => {
      // Check if narrator exists for this language
      const hasVoice = Boolean(
        langMappings[narratorId] ||
        langMappings[narratorId.replace('narrator_', '')]
      );

      if (hasVoice) {
        cardEl.classList.remove('disabled');
        noteEl.classList.add('hidden');
      } else {
        cardEl.classList.add('disabled');
        noteEl.classList.remove('hidden');
        noteEl.textContent = "Narrator not available for " + (state.voicesData.languages?.[state.selectedLanguage]?.name || state.selectedLanguage);

        // If currently selected narrator is disabled, auto-switch to the other
        if (state.selectedNarrator === narratorId) {
          const altId = narratorId === 'narrator_female' ? 'narrator_male' : 'narrator_female';
          selectNarrator(altId);
        }
      }
    };

    if (cardFemale && noteFemale) checkNarrator('narrator_female', cardFemale, noteFemale);
    if (cardMale && noteMale) checkNarrator('narrator_male', cardMale, noteMale);
  }

  btnProceedNarrator.addEventListener('click', () => goToStep(4));

  // --- Screen 4: Narrator Choice & "Hear a Sample" ---
  function selectNarrator(narratorId) {
    state.selectedNarrator = narratorId;

    document.querySelectorAll('.narrator-card').forEach(card => {
      if (card.getAttribute('data-narrator') === narratorId) {
        card.classList.add('selected');
      } else {
        card.classList.remove('selected');
      }
    });
  }

  if (cardFemale) {
    cardFemale.addEventListener('click', () => {
      if (!cardFemale.classList.contains('disabled')) {
        selectNarrator('narrator_female');
      }
    });
  }

  if (cardMale) {
    cardMale.addEventListener('click', () => {
      if (!cardMale.classList.contains('disabled')) {
        selectNarrator('narrator_male');
      }
    });
  }

  // Speed controls
  speedPills.forEach(pill => {
    pill.addEventListener('click', () => {
      speedPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.playbackSpeed = parseFloat(pill.getAttribute('data-speed'));
    });
  });

  // "Hear a sample" buttons
  document.querySelectorAll('.preview-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const narratorId = btn.getAttribute('data-narrator');
      const originalText = btn.innerHTML;
      btn.innerHTML = '⏳ Tuning...';

      try {
        // Send narrator ID (narrator_female / narrator_male) and language code
        const resp = await fetch('/api/preview-voice', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            language: state.selectedLanguage,
            narrator: narratorId
          })
        });

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || "Preview unavailable");
        }

        const data = await resp.json();
        // Stop any currently playing preview first
        previewAudio.pause();
        previewAudio.onended = null;
        // Force browser to reload the new src instead of replaying buffered audio
        previewAudio.src = '';
        previewAudio.load();
        previewAudio.src = data.audio_url;
        previewAudio.load();
        previewAudio.play();
        btn.innerHTML = '🔊 Playing...';

        previewAudio.onended = () => {
          btn.innerHTML = originalText;
        };
      } catch (err) {
        alert("Voice preview error: " + err.message);
        btn.innerHTML = originalText;
      }
    });
  });

  btnBindBook.addEventListener('click', () => startAudiobookBinding());

  // --- Screen 5: Binding (Progress Bar & Status) ---
  async function startAudiobookBinding() {
    goToStep(5);

    progressFill.style.width = '15%';
    updateBindingStatus('✦ Preparing manuscript pages (capped to 5 pages)...');

    // Gather selected pages
    const allPages = state.manuscript?.pages || [];
    const selectedTexts = [];
    for (let i = state.startPage - 1; i < state.endPage && i < allPages.length; i++) {
      if (allPages[i]?.text) {
        selectedTexts.push(allPages[i].text);
      }
    }

    // Send narrator ID (e.g. narrator_female / narrator_male) and language code
    // The backend picks the Gnani voice from voices.json; frontend never hard-codes it!
    const payload = {
      pages: selectedTexts,
      start_page: 1,
      end_page: selectedTexts.length,
      language: state.selectedLanguage,
      narrator: state.selectedNarrator,
      speed: state.playbackSpeed
    };

    const stages = [
      { pct: 30, text: '✦ Splitting text into natural sentence chunks (<= 650 chars)...' },
      { pct: 50, text: '✦ Checking disk cache for previously synthesized reels...' },
      { pct: 75, text: `✦ Synthesizing audio via Gnani Timbre v2.5 REST API...` },
      { pct: 90, text: '✦ Joining audio chunks with 250ms pauses (pydub + ffmpeg)...' }
    ];

    let stageIdx = 0;
    const stageTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        progressFill.style.width = `${stages[stageIdx].pct}%`;
        updateBindingStatus(stages[stageIdx].text);
        stageIdx++;
      }
    }, 1800);

    try {
      const resp = await fetch('/api/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      clearInterval(stageTimer);

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Synthesis failed');
      }

      const result = await resp.json();

      progressFill.style.width = '100%';
      updateBindingStatus('✦ Master MP3 Audiobook bound successfully!');

      setTimeout(() => {
        populateLibrary(result, selectedTexts.join('\n\n'));
        goToStep(6);
      }, 600);

    } catch (err) {
      clearInterval(stageTimer);
      alert("Binding Error: " + err.message);
      goToStep(4);
    }
  }

  function updateBindingStatus(msg) {
    bindingStatus.innerHTML = `<div class="status-line">${msg}</div>`;
  }

  // --- Screen 6: The Library (Audio Player & Download) ---
  function populateLibrary(result, fullText) {
    state.currentAudiobook = {
      ...result,
      text: fullText,
      title: state.manuscript?.filename || "KathaVaani Audiobook"
    };

    state.sessionShelf.unshift(state.currentAudiobook);
    renderSessionShelf();

    mainAudio.src = result.download_url;
    mainAudio.playbackRate = state.playbackSpeed;
    btnDownload.href = result.download_url;
    btnDownload.setAttribute('download', `${state.currentAudiobook.title}.mp3`);

    playerBookTitle.textContent = state.currentAudiobook.title;
    // Display narrator persona name without hardcoded Gnani voice names
    const narratorLabel = result.narrator === 'narrator_female' || result.narrator === 'female' ? 'Kavya' : 'Kabir';
    playerVoiceBadge.textContent = `${narratorLabel} (${result.language})`;

    readerText.textContent = fullText;
    readerLangBadge.textContent = result.language;

    turntableVinyl.classList.remove('spinning');
    playIcon.textContent = '▶';
  }

  btnPlayPause.addEventListener('click', () => {
    if (mainAudio.paused) {
      mainAudio.play();
      turntableVinyl.classList.add('spinning');
      playIcon.textContent = '⏸';
    } else {
      mainAudio.pause();
      turntableVinyl.classList.remove('spinning');
      playIcon.textContent = '▶';
    }
  });

  mainAudio.addEventListener('timeupdate', () => {
    if (mainAudio.duration) {
      const pct = (mainAudio.currentTime / mainAudio.duration) * 100;
      seekSlider.value = pct;
      currentTimeLabel.textContent = formatTime(mainAudio.currentTime);
      totalDurationLabel.textContent = formatTime(mainAudio.duration);
    }
  });

  mainAudio.addEventListener('ended', () => {
    turntableVinyl.classList.remove('spinning');
    playIcon.textContent = '▶';
  });

  seekSlider.addEventListener('input', () => {
    if (mainAudio.duration) {
      mainAudio.currentTime = (seekSlider.value / 100) * mainAudio.duration;
    }
  });

  btnBack10.addEventListener('click', () => {
    mainAudio.currentTime = Math.max(0, mainAudio.currentTime - 10);
  });

  btnFwd10.addEventListener('click', () => {
    mainAudio.currentTime = Math.min(mainAudio.duration || 0, mainAudio.currentTime + 10);
  });

  function formatTime(sec) {
    if (!sec || isNaN(sec)) return "0:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  function renderSessionShelf() {
    sessionShelfContainer.innerHTML = '';
    state.sessionShelf.forEach(item => {
      const el = document.createElement('div');
      el.className = 'session-book-item';
      const label = item.narrator.includes('female') ? 'Kavya' : 'Kabir';
      el.innerHTML = `
        <strong>${item.title}</strong>
        <span>${label} • ${item.language} • ${item.duration_seconds}s</span>
      `;
      el.addEventListener('click', () => {
        populateLibrary(item, item.text);
      });
      sessionShelfContainer.appendChild(el);
    });
  }

  if (btnNewBook) {
    btnNewBook.addEventListener('click', () => goToStep(2));
  }

  // --- Bootstrap ---
  fetchVoicesConfig();
  loadSampleBooks();

});
