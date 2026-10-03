// ============================================
// SHARMA CONTRACTORS — Main JavaScript
// ============================================

(function () {
  'use strict';

  // ─── NAVBAR SCROLL BEHAVIOUR ───
  const navbar = document.getElementById('navbar');
  if (navbar) {
    const handleScroll = () => {
      if (window.scrollY > 60) {
        navbar.classList.add('scrolled');
        navbar.classList.remove('transparent');
      } else {
        navbar.classList.remove('scrolled');
        navbar.classList.add('transparent');
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // ─── MOBILE MENU ───
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const isOpen = mobileMenu.classList.toggle('open');
      hamburger.classList.toggle('open', isOpen);
      hamburger.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      });
    });
  }

  // ─── HERO BG ANIMATION ───
  const heroBg = document.querySelector('.hero-bg');
  if (heroBg) {
    const img = new Image();
    img.src = getComputedStyle(heroBg).backgroundImage.slice(5, -2).replace(/"/g, '');
    img.onload = () => heroBg.classList.add('loaded');
  }

  // ─── AOS (ANIMATE ON SCROLL) ───
  function initAOS() {
    const elements = document.querySelectorAll('[data-aos]');
    if (!elements.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const delay = entry.target.dataset.aosDelay || 0;
          setTimeout(() => {
            entry.target.classList.add('aos-animate');
          }, parseInt(delay));
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    elements.forEach(el => observer.observe(el));
  }
  initAOS();

  // ─── COUNTER ANIMATION ───
  function animateCounter(el) {
    const target = parseInt(el.dataset.target || el.textContent);
    const suffix = el.dataset.suffix || '';
    const duration = 1800;
    const start = performance.now();
    const update = (time) => {
      const progress = Math.min((time - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target) + suffix;
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  const counters = document.querySelectorAll('[data-counter]');
  if (counters.length) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => {
      el.dataset.target = parseInt(el.textContent);
      counterObserver.observe(el);
    });
  }

  // ─── PORTFOLIO FILTER ───
  const filterBtns = document.querySelectorAll('.filter-btn');
  const portfolioItems = document.querySelectorAll('.portfolio-item');

  if (filterBtns.length && portfolioItems.length) {
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        portfolioItems.forEach(item => {
          if (filter === 'all' || item.dataset.category === filter) {
            item.style.display = 'block';
            item.style.animation = 'none';
            requestAnimationFrame(() => {
              item.style.animation = '';
            });
          } else {
            item.style.display = 'none';
          }
        });
      });
    });
  }

  // ─── GLIGHTBOX INIT ───
  if (typeof GLightbox !== 'undefined') {
    const lightbox = GLightbox({
      touchNavigation: true,
      loop: true,
      autoplayVideos: true,
      selector: '.glightbox',
      openEffect: 'fade',
      closeEffect: 'fade',
      slideEffect: 'slide',
    });
  }

  // ─── FLASH MESSAGE AUTO-DISMISS ───
  const flashMsgs = document.querySelectorAll('.flash-msg');
  flashMsgs.forEach(msg => {
    setTimeout(() => {
      msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      setTimeout(() => msg.remove(), 500);
    }, 4000);
  });

  // ─── CONTACT FORM VALIDATION ───
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      const name = contactForm.querySelector('[name=name]');
      const phone = contactForm.querySelector('[name=phone]');
      const message = contactForm.querySelector('[name=message]');
      let valid = true;

      [name, phone, message].forEach(field => {
        if (field && !field.value.trim()) {
          field.style.borderColor = '#ef4444';
          valid = false;
        } else if (field) {
          field.style.borderColor = '';
        }
      });

      if (!valid) {
        e.preventDefault();
        const firstInvalid = contactForm.querySelector('[style*="ef4444"]');
        if (firstInvalid) firstInvalid.focus();
      } else {
        e.preventDefault();
        alert('Thank you for reaching out! We will get in touch with you shortly.');
        contactForm.reset();
      }
    });

    contactForm.querySelectorAll('input, textarea, select').forEach(field => {
      field.addEventListener('input', () => {
        field.style.borderColor = '';
      });
    });
  }

  // ─── LAZY LOADING ───
  if ('loading' in HTMLImageElement.prototype) {
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
    });
  } else {
    const lazyObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          lazyObserver.unobserve(img);
        }
      });
    });
    document.querySelectorAll('img[data-src]').forEach(img => lazyObserver.observe(img));
  }

  // ─── ADMIN: IMAGE UPLOAD PREVIEW ───
  const imageInput = document.getElementById('imageInput');
  const previewGrid = document.getElementById('imagePreviewGrid');
  if (imageInput && previewGrid) {
    imageInput.addEventListener('change', () => {
      const files = Array.from(imageInput.files);
      files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const item = document.createElement('div');
          item.className = 'image-preview-item';
          item.innerHTML = `
            <img src="${e.target.result}" alt="Preview">
            <div class="set-cover" onclick="setCover(this)">Set as Cover</div>
          `;
          previewGrid.appendChild(item);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  window.setCover = function(el) {
    document.querySelectorAll('.image-preview-item').forEach(item => {
      item.classList.remove('is-cover');
      const btn = item.querySelector('.set-cover');
      if (btn) btn.textContent = 'Set as Cover';
    });
    el.closest('.image-preview-item').classList.add('is-cover');
    el.textContent = '✓ Cover Image';
    const index = Array.from(document.querySelectorAll('.image-preview-item')).indexOf(el.closest('.image-preview-item'));
    const coverInput = document.getElementById('coverIndex');
    if (coverInput) coverInput.value = index;
  };

  // ─── ADMIN: TOGGLE FEATURED ───
  document.querySelectorAll('[data-toggle-featured]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const projectId = btn.dataset.toggleFeatured;
      try {
        const res = await fetch(`/admin/projects/${projectId}/toggle-featured`, { method: 'POST' });
        const data = await res.json();
        btn.textContent = data.featured ? '★ Featured' : '☆ Feature';
        btn.style.color = data.featured ? '#B8965A' : '';
      } catch (e) { console.error(e); }
    });
  });

  // ─── ADMIN: TOGGLE STATUS ───
  document.querySelectorAll('[data-toggle-status]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const projectId = btn.dataset.toggleStatus;
      try {
        const res = await fetch(`/admin/projects/${projectId}/toggle-status`, { method: 'POST' });
        const data = await res.json();
        const badge = btn.closest('tr').querySelector('.status-badge');
        if (badge) {
          badge.textContent = data.status === 'published' ? 'Published' : 'Draft';
          badge.className = `badge status-badge ${data.status === 'published' ? 'badge-green' : 'badge-gray'}`;
        }
        btn.textContent = data.status === 'published' ? 'Unpublish' : 'Publish';
      } catch (e) { console.error(e); }
    });
  });

  // ─── ADMIN: DELETE IMAGE ───
  document.querySelectorAll('[data-delete-image]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Remove this image?')) return;
      const imageId = btn.dataset.deleteImage;
      try {
        const res = await fetch(`/admin/images/${imageId}/delete`, { method: 'POST' });
        const data = await res.json();
        if (data.success) btn.closest('.image-preview-item').remove();
      } catch (e) { console.error(e); }
    });
  });

  // ─── ADMIN SIDEBAR MOBILE ───
  const sidebarToggle = document.getElementById('sidebarToggle');
  const adminSidebar = document.getElementById('adminSidebar');
  if (sidebarToggle && adminSidebar) {
    sidebarToggle.addEventListener('click', () => {
      adminSidebar.classList.toggle('open');
    });
  }

  // ─── SMOOTH SCROLL FOR ANCHOR LINKS ───
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

})();
