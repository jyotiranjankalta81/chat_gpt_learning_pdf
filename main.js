function autosize(textarea) {
  const prev = textarea.style.height;
  textarea.style.height = 'auto';
  textarea.style.height = Math.max(textarea.scrollHeight, 160) + 'px';
  // avoid unnecessary layout churn
  if (prev === textarea.style.height) return;
}

for (const ta of document.querySelectorAll('.card__textarea')) {
  ta.addEventListener('input', () => autosize(ta));
  // initial
  autosize(ta);
}
