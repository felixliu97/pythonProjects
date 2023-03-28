import React, { useState } from "react";
import "./App.css";
import Sidebar from "./Sidebar";
import { FaDatabase, FaServer, FaCloud, FaCode, FaChartLine, FaStream } from "react-icons/fa";

function App() {
  const sections = [
    {
      name: "About Me",
      content: (
        <p>
          Experienced Data Engineer with a demonstrated history of working in IT industry. Skilled in Business Intelligence, Data & Analytics, Data Warehousing and Cloud. Strong information technology professional with a Master of Information Technology (MIT) majoring in Database System, Networking & Artificial Intelligence from University of New South Wales.
          <br /><br />
          A passionate, result driven person delivering high quality results. Love a wide range of sports including soccer, basketball, table tennis and many others.
        </p>
      )
    },
    {
      name: "Knowledge Area",
      content: (
        <>
          <div className="icon-text">
            <FaCode />
            <span>Programming Languages: SQL, Python, Java, Shell</span>
          </div>
          <div className="icon-text">
            <FaDatabase />
            <span>Structured Databases: SQL Server, PostgreSQL DB, MySQL DB, etc.</span>
          </div>
          <div className="icon-text">
            <FaDatabase />
            <span>No-SQL Databases: MongoDB, Cosmos DB, Dynamo DB, etc.</span>
          </div>
          <div className="icon-text">
            <FaServer />
            <span>Data warehouses: Redshift, Snowflake, Synapse Analytics</span>
          </div>
          <div className="icon-text">
            <FaStream />
            <span>Streaming: Kafka, AWS Kinesis</span>
          </div>
          <div className="icon-text">
            <FaChartLine />
            <span>Visualization: Tableau, PowerBI, Logi Info Studio, Redash</span>
          </div>
          <div className="icon-text">
            <FaCloud />
            <span>Cloud: AWS, Azure</span>
          </div>
        </>
      )
    },
    {
      name: "Industries",
      content: <h2>Industries Content</h2>
    },
    {
      name: "Careers",
      content: <h2>Careers Content</h2>
    },
    {
      name: "Education",
      content: <h2>Education Content</h2>
    },
    {
      name: "Certifications",
      content: <h2>Certifications Content</h2>
    }
  ];

  const [currentSection, setCurrentSection] = useState(sections[0]);

  const setSection = sectionName => {
    const section = sections.find(sec => sec.name === sectionName);
    setCurrentSection(section);
  };

  return (
    <div className="App">
      <Sidebar sections={sections} setSection={setSection} />
      <div className="content">
        <h1>{currentSection.name}</h1>
        {currentSection.content}
      </div>
    </div>
  );
}

export default App;
