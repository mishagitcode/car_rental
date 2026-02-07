(() => {
  const rentalForm = document.querySelector("[data-rental-form]");
  if (!rentalForm) {
    return;
  }

  const issueInput = rentalForm.querySelector("input[name='date_issue']");
  const expectedInput = rentalForm.querySelector(
    "input[name='expected_return_date']"
  );

  const syncExpectedMin = () => {
    if (!issueInput || !expectedInput) {
      return;
    }
    expectedInput.min = issueInput.value;
    if (expectedInput.value && expectedInput.value < issueInput.value) {
      expectedInput.value = issueInput.value;
    }
  };

  issueInput?.addEventListener("change", syncExpectedMin);
  syncExpectedMin();
})();
