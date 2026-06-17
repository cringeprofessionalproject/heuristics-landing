// Theme Toggle Logic
const themeToggleBtn = document.getElementById('theme-toggle');
const root = document.documentElement;

// Check user preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const savedTheme = localStorage.getItem('theme');

if (savedTheme) {
  root.setAttribute('data-theme', savedTheme);
} else if (prefersDark) {
  root.setAttribute('data-theme', 'dark');
} else {
  root.setAttribute('data-theme', 'light');
}

themeToggleBtn.addEventListener('click', () => {
  const currentTheme = root.getAttribute('data-theme') || (prefersDark ? 'dark' : 'light');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  
  root.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
});

// Reveal on Scroll Logic
const revealElements = document.querySelectorAll('.reveal');

const revealCallback = (entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active');
      // Optional: stop observing once revealed
      // observer.unobserve(entry.target);
    }
  });
};

const revealOptions = {
  threshold: 0.15,
  rootMargin: "0px 0px -50px 0px"
};

const revealObserver = new IntersectionObserver(revealCallback, revealOptions);

revealElements.forEach(el => {
  revealObserver.observe(el);
});
