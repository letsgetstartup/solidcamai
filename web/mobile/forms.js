export const FORM_TEMPLATES = {
    downtime: {
        title: "Report Downtime",
        fields: [
            {
                id: "reason_cat", label: "Reason Category", type: "select", options: [
                    "Setup / Changeover", "Tooling", "Material", "Program / NC", "Maintenance", "Other"
                ]
            },
            { id: "reason_detail", label: "Detail", type: "text", placeholder: "e.g. Tool Break" },
            { id: "duration", label: "Estimated Duration (min)", type: "number" },
            { id: "notes", label: "Notes", type: "textarea" }
        ]
    },
    quality: {
        title: "Report Quality Issue",
        fields: [
            {
                id: "issue_type", label: "Issue Type", type: "select", options: [
                    "Scrap", "Rework", "Measurement", "Surface Finish"
                ]
            },
            { id: "part_count", label: "Quantity Affected", type: "number", value: 1 },
            { id: "notes", label: "Notes", type: "textarea" }
        ]
    },
    maintenance: {
        title: "Maintenance Request",
        fields: [
            {
                id: "symptom", label: "Symptom", type: "select", options: [
                    "Noise", "Leak", "Vibration", "Error Code", "Other"
                ]
            },
            { id: "severity", label: "Severity", type: "select", options: ["Low", "Medium", "High (Stop)"] },
            { id: "notes", label: "Description", type: "textarea" }
        ]
    }
};

export function renderForm(template, container) {
    container.innerHTML = "";
    template.fields.forEach(field => {
        const wrapper = document.createElement("div");

        const label = document.createElement("label");
        label.textContent = field.label;
        wrapper.appendChild(label);

        let input;
        if (field.type === "select") {
            input = document.createElement("select");
            field.options.forEach(opt => {
                const o = document.createElement("option");
                o.value = opt;
                o.textContent = opt;
                input.appendChild(o);
            });
        } else if (field.type === "textarea") {
            input = document.createElement("textarea");
        } else {
            input = document.createElement("input");
            input.type = field.type;
        }

        if (field.placeholder) input.placeholder = field.placeholder;
        if (field.value !== undefined) input.value = field.value;
        input.id = `f_${field.id}`;

        wrapper.appendChild(input);
        container.appendChild(wrapper);
    });
}

export function extractFormData(template) {
    const data = {};
    template.fields.forEach(field => {
        const el = document.getElementById(`f_${field.id}`);
        if (el) data[field.id] = el.value;
    });
    return data;
}
