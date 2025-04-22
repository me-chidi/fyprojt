document.addEventListener("DOMContentLoaded", () => {
  // Function to set up a dropdown with a GO button and clickable options
  const setupDropdown = (dropdownSearchId, goBtnId, dropdownClass) => {
    const dropdownBtn = document.querySelector(
      `.${dropdownClass} .dropdown-btn`
    );
    const dropdownContent = document.querySelector(
      `.${dropdownClass} .dropdown-content`
    );
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
      options.forEach((option) => {
        const text = option.textContent || option.innerText;
        option.style.display = text.toLowerCase().includes(filter)
          ? "block"
          : "none";
      });
    });

    // Handle GO button functionality
    goButton.addEventListener("click", () => {
      const selectedValue = searchInput.value.trim();
      if (selectedValue) {
        if (goBtnId === "goBtn2") {
          updateIndividualNode(selectedValue, "OFF");
          alert(`You Turned OFF Node ${selectedValue}!`);
        } else {
          updateIndividualNode(selectedValue, "ON");
          alert(`You Turned ON Node ${selectedValue}!`);
        }
        dropdownBtn.textContent = `Selected: ${selectedValue}`; // Update the button text
        dropdownContent.style.display = "none"; // Close the dropdown
        searchInput.value = ""; // Clear the search input
        options.forEach((option) => (option.style.display = "block")); // Reset options
      } else {
        alert("Please enter a valid node!");
      }
    });

    // Handle option clicks directly
    options.forEach((option) => {
      option.addEventListener("click", (event) => {
        const selectedValue = event.target.textContent.trim();
        if (dropdownSearchId === "dropdownSearch2") {
          updateIndividualNode(selectedValue, "OFF");
          alert(`You Turned OFF Node ${selectedValue}!`);
        } else {
          updateIndividualNode(selectedValue, "ON");
          alert(`You Turned ON Node ${selectedValue}!`);
        }
        // updateIndividualNode(selectedValue);
        dropdownBtn.textContent = `Selected: ${selectedValue}`; // Update the button text
        dropdownContent.style.display = "none"; // Close the dropdown
        searchInput.value = ""; // Clear the search input
        options.forEach((option) => (option.style.display = "block")); // Reset options
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
  setupDropdown("dropdownSearch1", "goBtn1", "btn:first-child .dropdown");

  // Set up "TURN OFF" dropdown
  setupDropdown("dropdownSearch2", "goBtn2", "btn:last-child .dropdown");

  const allOffBtn = document.getElementById("all-off");
  const allOnBtn = document.getElementById("all-on");

  allOffBtn.addEventListener("click", () => {
    updateAllNode("OFF");
    alert(`You Turned OFF all Nodes!`);
  });
  
  allOnBtn.addEventListener("click", () => {
    updateAllNode("ON");
    alert(`You Turned ON all Nodes!`);
  });
});

const updateIndividualNode = async (nodeId, status) => {
  try {
    if (status === "ON") {
      to_serial = "atv";
    }else {
      to_serial = "dtv";
    }
    const response = await fetch(`http://127.0.0.1:5000/update/${nodeId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ node_id: nodeId, to_serial: to_serial, status: status }),
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Response data:", data);
    } else {
      const errorData = await response.json();
      console.error("Error:", errorData.error || "Unknown error");  
    }
  } catch (error) {
    console.error("Error occurred while updating individual node:", error);
  }
};

const updateAllNode = async (status) => {
  try {
    const response = await fetch(`http://127.0.0.1:5000/update_all`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: status }),
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Response data:", data);
    } else {
      const errorData = await response.json();
      console.error("Error:", errorData.error || "Unknown error");
    }
  } catch (error) {
    console.error("Error occurred while updating all nodes:", error);
  }
};
