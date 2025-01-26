document.addEventListener("DOMContentLoaded", () => {
    // Function to set up a dropdown with a GO button and clickable options
    const setupDropdown = (dropdownSearchId, goBtnId, dropdownClass) => {
      const dropdownBtn = document.querySelector(`.${dropdownClass} .dropdown-btn`);
      const dropdownContent = document.querySelector(`.${dropdownClass} .dropdown-content`);
      const searchInput = document.getElementById(dropdownSearchId);
      const goButton = document.getElementById(goBtnId);
      const options = dropdownContent.querySelectorAll("a");
  
      // Toggle dropdown visibility
      dropdownBtn.addEventListener("click", () => {
        dropdownContent.style.display =
          dropdownContent.style.display === "block" ? "none" : "block";
      });
  
      // Filter options based on search input
      searchInput.addEventListener("input", () => {
        const filter = searchInput.value.toLowerCase();
        options.forEach(option => {
          const text = option.textContent || option.innerText;
          option.style.display = text.toLowerCase().includes(filter) ? "block" : "none";
        });
      });
  
      // Handle GO button functionality
      goButton.addEventListener("click", () => {
        const selectedValue = searchInput.value.trim();
        if (selectedValue) {
          alert(`You selected: ${selectedValue}`);
          dropdownBtn.textContent = `Selected: ${selectedValue}`; // Update the button text
          dropdownContent.style.display = "none"; // Close the dropdown
          searchInput.value = ""; // Clear the search input
          options.forEach(option => option.style.display = "block"); // Reset options
        } else {
          alert("Please enter a valid node!");
        }
      });
  
      // Handle option clicks directly
      options.forEach(option => {
        option.addEventListener("click", (event) => {
          const selectedValue = event.target.textContent.trim();
          alert(`You selected: ${selectedValue}`);
          dropdownBtn.textContent = `Selected: ${selectedValue}`; // Update the button text
          dropdownContent.style.display = "none"; // Close the dropdown
          searchInput.value = ""; // Clear the search input
          options.forEach(option => option.style.display = "block"); // Reset options
        });
      });
  
      // Close dropdown when clicking outside
      document.addEventListener("click", (event) => {
        if (!event.target.closest(`.${dropdownClass}`)) {
          dropdownContent.style.display = "none";
        }
      });
    };
  
    // Set up "TURN ON" dropdown
    setupDropdown("dropdownSearch", "goBtn1", "btn:first-child .dropdown");
  
    // Set up "TURN OFF" dropdown
    setupDropdown("dropdownSearch2", "goBtn2", "btn:last-child .dropdown");
  });
  