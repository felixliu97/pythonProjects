import React from "react";

function Sidebar(props) {
  return (
    <div className="sidebar">
      {props.sections.map((section, index) => (
        <button key={index} onClick={() => props.setSection(section.name)}>
          {section.name}
        </button>
      ))}
    </div>
  );
}

export default Sidebar;
