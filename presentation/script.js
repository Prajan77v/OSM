document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const slides = document.querySelectorAll('.slide');
  const slideIndexSpan = document.getElementById('slide-index');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const notesBtn = document.getElementById('notes-btn');
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  const notesPanel = document.getElementById('notes-panel');
  const closeNotesBtn = document.getElementById('close-notes-btn');
  const notesContent = document.getElementById('notes-content');
  const clockElement = document.getElementById('clock');
  const presentationContainer = document.querySelector('.presentation-container');

  let currentSlideIndex = 0;
  let direction = 'next'; // 'next' or 'prev'

  // Initialize
  updateSlides();
  startClock();

  // Navigation Logic
  function updateSlides() {
    slides.forEach((slide, index) => {
      // Reset classes first
      slide.classList.remove('active', 'slide-exit-left', 'slide-exit-right');

      if (index === currentSlideIndex) {
        slide.classList.add('active');
        // Update notes content
        const notes = slide.getAttribute('data-notes') || 'No notes for this slide.';
        notesContent.textContent = notes;
      } else if (index < currentSlideIndex) {
        // Slide is on the left
        slide.classList.add('slide-exit-left');
      } else {
        // Slide is on the right
        slide.classList.add('slide-exit-right');
      }
    });

    // Update Counter (formatted as 01 / 08)
    const formattedCurrent = String(currentSlideIndex + 1).padStart(2, '0');
    const formattedTotal = String(slides.length).padStart(2, '0');
    slideIndexSpan.textContent = `${formattedCurrent} / ${formattedTotal}`;
  }

  function nextSlide() {
    if (currentSlideIndex < slides.length - 1) {
      direction = 'next';
      currentSlideIndex++;
      updateSlides();
    }
  }

  function prevSlide() {
    if (currentSlideIndex > 0) {
      direction = 'prev';
      currentSlideIndex--;
      updateSlides();
    }
  }

  // Visual Click Feedback Helper
  function animateClick(button, clickClass = 'clicked') {
    button.classList.add(clickClass);
    setTimeout(() => {
      button.classList.remove(clickClass);
    }, 150); // duration of active flash
  }

  // Event Listeners for Nav Buttons with click animation
  nextBtn.addEventListener('click', (e) => {
    animateClick(nextBtn);
    nextSlide();
  });

  prevBtn.addEventListener('click', (e) => {
    animateClick(prevBtn);
    prevSlide();
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
      e.preventDefault(); // Stop spacebar scrolling
      animateClick(nextBtn);
      nextSlide();
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      animateClick(prevBtn);
      prevSlide();
    } else if (e.key.toLowerCase() === 'n') {
      animateClick(notesBtn, 'clicked-magenta');
      toggleNotes();
    } else if (e.key.toLowerCase() === 'f') {
      animateClick(fullscreenBtn, 'clicked-magenta');
      toggleFullscreen();
    }
  });

  // Notes Panel Actions
  function toggleNotes() {
    notesPanel.classList.toggle('open');
    presentationContainer.classList.toggle('notes-open');
    if (notesPanel.classList.contains('open')) {
      notesBtn.textContent = '🗎 HIDE NOTES';
    } else {
      notesBtn.textContent = '🗎 SHOW NOTES';
    }
  }

  notesBtn.addEventListener('click', () => {
    animateClick(notesBtn, 'clicked-magenta');
    toggleNotes();
  });

  closeNotesBtn.addEventListener('click', () => {
    notesPanel.classList.remove('open');
    presentationContainer.classList.remove('notes-open');
    notesBtn.textContent = '🗎 SHOW NOTES';
  });

  // Fullscreen Mode Actions
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  }

  fullscreenBtn.addEventListener('click', () => {
    animateClick(fullscreenBtn, 'clicked-magenta');
    toggleFullscreen();
  });

  // Clock Update
  function startClock() {
    function refreshClock() {
      const now = new Date();
      const hrs = String(now.getHours()).padStart(2, '0');
      const mins = String(now.getMinutes()).padStart(2, '0');
      const secs = String(now.getSeconds()).padStart(2, '0');
      clockElement.textContent = `${hrs}:${mins}:${secs}`;
    }
    refreshClock();
    setInterval(refreshClock, 1000);
  }
});
