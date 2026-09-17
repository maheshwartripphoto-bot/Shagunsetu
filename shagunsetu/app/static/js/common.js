(function () {
  'use strict';

  // 1. Falling Petal Generator
  function initPetals() {
    const colors = [
      'radial-gradient(circle, #f37021 20%, #e25822 80%)',
      'radial-gradient(circle, #ffc107 20%, #e59400 80%)',
      'radial-gradient(circle, #ffccd5 20%, #e85d75 80%)'
    ];

    setInterval(() => {
      const petal = document.createElement('div');
      petal.className = 'petal-particle';
      const startX = Math.random() * 100;
      const duration = Math.floor(Math.random() * 6) + 7;
      petal.style.cssText = `
        position: fixed; top: -20px; left: ${startX}vw; width: 14px; height: 18px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        border-radius: 50% 50% 50% 0; pointer-events: none; z-index: 999;
        transition: transform ${duration}s linear, top ${duration}s linear;
      `;
      document.body.appendChild(petal);
      requestAnimationFrame(() => {
        petal.style.top = '105vh';
        petal.style.transform = `rotate(${Math.random() * 720}deg)`;
      });
      setTimeout(() => petal.remove(), duration * 1000);
    }, 1500);
  }

  // 2. RSVP Attendance Selector Logic
  function initRsvpLogic() {
    const sel = document.querySelector('select[name="attending"]');
    const cnt = document.querySelector('input[name="guest_count"]');
    if (sel && cnt) {
      sel.addEventListener('change', () => {
        cnt.disabled = sel.value === 'No';
        cnt.value = sel.value === 'No' ? 0 : 1;
        cnt.style.opacity = sel.value === 'No' ? '0.5' : '1';
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initPetals();
    initRsvpLogic();
  });
})();

// Preset Shagun Clicker
function selectShagunAmount(amt) {
  const inp = document.getElementById('shagun-amount-input');
  if (inp) inp.value = amt;
}

// UPI Intent Trigger & Dynamic QR Display
function triggerUPIPayment(upiId, payeeName) {
  const amt = document.getElementById('shagun-amount-input')?.value || 501;
  const upiUrl = `upi://pay?pa=${encodeURIComponent(upiId)}&pn=${encodeURIComponent(payeeName)}&am=${amt}&cu=INR&tn=Wedding%20Shagun`;
  
  // Mobile deep link trigger
  window.location.href = upiUrl;

  // Desktop QR Fallback
  const qrImg = document.getElementById('shagun-qr-image');
  const qrBox = document.getElementById('shagun-qr-modal');
  if (qrImg && qrBox) {
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(upiUrl)}`;
    qrBox.style.display = 'block';
  }
}

// Registry Modal
function openRegistryContribution(itemId, itemName, remainingAmt) {
  const modal = document.getElementById('registry-modal');
  if (modal) {
    document.getElementById('registry-form').action = `/registry/contribute/${itemId}`;
    document.getElementById('registry-modal-title').innerText = `Contribute to: ${itemName}`;
    document.getElementById('registry-amount-input').value = remainingAmt;
    modal.style.display = 'flex';
  }
}

function closeRegistryModal() {
  const modal = document.getElementById('registry-modal');
  if (modal) modal.style.display = 'none';
}

// Native WhatsApp Invitation Sharing
function shareOnWhatsApp(coupleName, url) {
  const link = url || window.location.href;
  const msg = `🌸 *श्री गणेशाय नमः* 🌸\n\nYou and your family are cordially invited to celebrate the auspicious wedding of *${coupleName}*.\n\n🔗 *E-Patrika, Shagun Desk & Registry:* ${link}`;
  window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`, '_blank');
}
