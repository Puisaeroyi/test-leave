/**
 * Cascading dropdowns for Django admin - Entity → Location → Department
 * Preloads all entity/location/department data on page load
 */
(function() {
    'use strict';

    // Preload data from global variable (set by Django form)
    let entityData = window.ENTITY_LOCATION_DATA || {};

    function initCascadingDropdowns() {
        const entitySelect = document.querySelector('select[name="entity"]');
        const locationSelect = document.querySelector('select[name="location"]');
        const departmentSelect = document.querySelector('select[name="department"]');

        if (!entitySelect) return;

        // Store all original options
        const allLocations = locationSelect ? Array.from(locationSelect.options).map(opt => ({
            value: opt.value,
            text: opt.text,
            entity: opt.dataset?.entity || ''
        })) : [];
        const allDepartments = departmentSelect ? Array.from(departmentSelect.options).map(opt => ({
            value: opt.value,
            text: opt.text,
            entity: opt.dataset?.entity || ''
        })) : [];

        function updateDropdowns() {
            const selectedEntity = entitySelect.value;

            // Filter locations by entity
            if (locationSelect) {
                const currentValue = locationSelect.value;
                locationSelect.innerHTML = '<option value="">---------</option>';
                allLocations.forEach(loc => {
                    if (!selectedEntity || loc.entity === '' || loc.entity === selectedEntity) {
                        const opt = document.createElement('option');
                        opt.value = loc.value;
                        opt.textContent = loc.text;
                        opt.dataset.entity = loc.entity;
                        locationSelect.appendChild(opt);
                    }
                });
                // Restore value if still valid
                if (currentValue) {
                    const exists = Array.from(locationSelect.options).some(opt => opt.value === currentValue);
                    if (exists) locationSelect.value = currentValue;
                }
            }

            // Filter departments by entity
            if (departmentSelect) {
                const currentValue = departmentSelect.value;
                departmentSelect.innerHTML = '<option value="">---------</option>';
                allDepartments.forEach(dept => {
                    if (!selectedEntity || dept.entity === '' || dept.entity === selectedEntity) {
                        const opt = document.createElement('option');
                        opt.value = dept.value;
                        opt.textContent = dept.text;
                        opt.dataset.entity = dept.entity;
                        departmentSelect.appendChild(opt);
                    }
                });
                // Restore value if still valid
                if (currentValue) {
                    const exists = Array.from(departmentSelect.options).some(opt => opt.value === currentValue);
                    if (exists) departmentSelect.value = currentValue;
                }
            }
        }

        // Listen for entity changes
        entitySelect.addEventListener('change', updateDropdowns);

        // Run on page load
        updateDropdowns();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCascadingDropdowns);
    } else {
        initCascadingDropdowns();
    }
})();
