import os
from dotenv import load_dotenv, find_dotenv

from langchain_community.vectorstores import Pinecone
import pinecone

# from langchain_openai import OpenAI
from langchain_community.llms import Cohere
from langchain_community.embeddings import CohereEmbeddings
from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever

from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains.question_answering import load_qa_chain

# DOTENV
load_dotenv(find_dotenv())

def pretty_print_docs(docs):
    return (
        f"\n\n---\n\n".join(
            [f"Document {i + 1} :\n\n" + str(d.metadata) + "\n\n" + d.page_content.strip() for i, d in enumerate(docs)]
        )
    )


class ChatBot:
    def __init__(self):

        self.COHERE_API_KEY = os.environ['COHERE_API_KEY']
        # self.OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
        # Initialize pinecone
        self.index_name = "langchain"

        pinecone.init(
            api_key=os.environ['PINECONE_API_KEY'],
            environment=os.environ['PINECONE_ENVIRONMENT']
        )
        self.index = pinecone.Index(self.index_name)

        # Set up the conversation chain
        self.embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=self.COHERE_API_KEY)
        self.llm = Cohere(model="command-nightly", temperature=0.2, cohere_api_key=self.COHERE_API_KEY, max_tokens=2048)
        # self.llm = OpenAI(openai_api_key=self.OPENAI_API_KEY, model_name="gpt-4")
        self.template = """You are an AI assistant for answering questions based solely on documents.
            You are given the following extracted parts of a long document in  <doc> </doc> xml tags and a question that requires those contexts. 
            Provide a conversational answer. Chat history is in <history> </history xml tags.
            If you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer.
            =========
            <doc>
            {context}
            </doc>
            =========
            <history>
            {chat_history}
            </history>
            =========
            User: {question}
            AI:
            """

        self.qa_prompt_template = PromptTemplate(
            input_variables=["question", "context", "chat_history"],
            template=self.template
        )


        self.summary_prompt_template = """
        Current summary:
        {summary}
        
        new lines of conversation:
        {new_lines}
        
        New summary:
        """

        summary_prompt = PromptTemplate(
            input_variables=["summary", "new_lines"],
            template=self.summary_prompt_template
        )

        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            memory_key="chat_history",
            input_key="question",
            max_token=4000,  # after 4000 token, summary of the conversation will be created and stored in moving_summary_buffer
            prompt=summary_prompt,
            moving_summary_buffer="summary",    # sets the summary of the memory
            )

        self.chain = load_qa_chain(
            llm=self.llm,
            chain_type="stuff",
            memory=self.memory,
            prompt=self.qa_prompt_template)

        # 2 stage RAG with CohereRerank (reduces "lost in the middle")
        self.compressor = CohereRerank(model="rerank-multilingual-v2.0",
                                  cohere_api_key=self.COHERE_API_KEY,
                                  user_agent="langchain",
                                  top_n=4)

    def ask(self, query, namespace):
        docsearch = Pinecone.from_existing_index(self.index_name, self.embeddings, namespace=namespace)
        compression_retriever = ContextualCompressionRetriever(base_compressor=self.compressor,
                                                               base_retriever=docsearch.as_retriever(
                                                                   search_type="similarity",
                                                                   search_kwargs={"k": 20}
                                                                    )
                                                               )

        compressed_docs = compression_retriever.get_relevant_documents(query)
        answer = self.chain.invoke(
            input={"input_documents": compressed_docs, "question": query},
            return_only_outputs=True
        )

        return {
                "message": answer["output_text"],
                "docs": pretty_print_docs(compressed_docs),
                "history": str(self.chain.memory.buffer)
                }

