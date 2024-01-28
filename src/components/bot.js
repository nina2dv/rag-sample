import React, { useState }  from "react";
import axios from "axios";
import ReactMarkdown from 'react-markdown';

function Bot() {
  const [output, setOutput] = useState("")
  const [docs, setDocs] = useState("")
  const [text, setText] = useState("")
  const [chatHistory, setChatHistory] = useState([]);
  //const [course, setCourse] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false);

  var note = "Chat bot responses may be incorrect \nLLM is Cohere command-nightly\nEmbedding model is Cohere embed-english-v3.0";

  function handleChangeText(e) {
    setText(e.target.value);
  };
//   function handleChangeCourse(e) {
//     setCourse(e.target.value);
//   };
    const [isAccordionOpen, setIsAccordionOpen] = useState(false);
    function toggleAccordion() {
    setIsAccordionOpen(!isAccordionOpen);
    }

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitting(true); // Disable further submissions
    const queryValue = document.getElementById("query").value.trim();
    //const courseValue = document.getElementById("course").value.trim().toLowerCase();

    if (queryValue) {
        const token = process.env.REACT_APP_API_KEY;


        // axios.post("http://localhost:5000/query", {
        axios.post("https://rag-chatbot-flask.onrender.com/query", {
            query: queryValue, 
            //course: courseValue, 
        }, {
            headers: {
                // Include the Authorization header with the token
                'Authorization': `Bearer ${token}`
            }
        })
        .then((res) => {
            const newEntry = {
                query: queryValue,
                response: res.data.message,
            };
            console.log(res.data);
            setChatHistory([...chatHistory, newEntry]); // Add new entry to chat history
            setOutput(res.data.message); // 'message' is the key in the response
            setDocs(res.data.docs);
        })
        .catch((error) => {
            console.error("There was an error!", error);
            setOutput("Error: " + error.message);
            setDocs("Error: " + error.message);
        })
        .finally(() => {
            setIsSubmitting(false); // Re-enable submission after request completion
        });
    } else {
        console.error("Query must not be empty");
        setOutput("Query must not be empty");
    }};

  return (
<div className="chat-container">
  <div className="chat-box">
    <div className="chat-header">
      <h2>ChatBot</h2>
    </div>
    <div className="chat-history">
            {chatHistory.map((entry, index) => (
        <div key={index} className="chat-entry">

                <ReactMarkdown className="user-query">
                {"You: " + entry.query}
                </ReactMarkdown>

            <ReactMarkdown className="bot-response">{entry.response}</ReactMarkdown>
        </div>
        ))}
    </div>
    <div className="chat-input">
      <form onSubmit={handleSubmit}>
        <textarea
          id="query"
          name="query"
          placeholder="Enter query here..."
          onChange={handleChangeText}
          value={text}
        />
        <button type="submit" disabled={isSubmitting}>Send</button>
      </form>
    </div>
  </div>

  <div className="accordion-container">
      <button className="accordion" onClick={toggleAccordion}>
        Retrieved Documents
      </button>
      <div className={`panel ${isAccordionOpen ? "open" : ""}`}>
        <ReactMarkdown>{docs}</ReactMarkdown>
      </div>
    </div>

  <div className="chat-notes">

    {note.split("\n").map((item, index) => (
    <p  key={index}>{item}</p>
    ))}
  </div>
  
</div>
   
  );
}

export default Bot;