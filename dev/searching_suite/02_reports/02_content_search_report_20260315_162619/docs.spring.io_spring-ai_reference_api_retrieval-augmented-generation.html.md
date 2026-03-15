# Retrieval Augmented Generation :: Spring AI Reference
**URL:** https://docs.spring.io/spring-ai/reference/api/retrieval-augmented-generation.html
**Domain:** docs.spring.io
**Score:** 3.2
**Source:** scraped
**Query:** query expansion RAG retrieval augmented generation

---

Search ⌘ + k
# Retrieval Augmented Generation
Retrieval Augmented Generation (RAG) is a technique useful to overcome the limitations of large language models that struggle with long-form content, factual accuracy, and context-awareness.
Spring AI supports RAG by providing a modular architecture that allows you to build custom RAG flows yourself or use out-of-the-box RAG flows using the `Advisor` API.
Learn more about Retrieval Augmented Generation in the [concepts](https://docs.spring.io/spring-ai/reference/concepts.html#concept-rag) section.   
---  
##  Advisors
Spring AI provides out-of-the-box support for common RAG flows using the `Advisor` API.
To use the `QuestionAnswerAdvisor` or `VectorStoreChatMemoryAdvisor`, you need to add the `spring-ai-advisors-vector-store` dependency to your project:
```
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-advisors-vector-store</artifactId>
</dependency>
Copied!

```

###  QuestionAnswerAdvisor
A vector database stores data that the AI model is unaware of. When a user question is sent to the AI model, a `QuestionAnswerAdvisor` queries the vector database for documents related to the user question.
The response from the vector database is appended to the user text to provide context for the AI model to generate a response.
Assuming you have already loaded data into a `VectorStore`, you can perform Retrieval Augmented Generation (RAG) by providing an instance of `QuestionAnswerAdvisor` to the `ChatClient`.
```
ChatResponse response = ChatClient.builder(chatModel)
        .build().prompt()
        .advisors(QuestionAnswerAdvisor.builder(vectorStore).build())
        .user(userText)
        .call()
        .chatResponse();
Copied!

```

In this example, the `QuestionAnswerAdvisor` will perform a similarity search over all documents in the Vector Database. To restrict the types of documents that are searched, the `SearchRequest` takes an SQL like filter expression that is portable across all `VectorStores`.
This filter expression can be configured when creating the `QuestionAnswerAdvisor` and hence will always apply to all `ChatClient` requests, or it can be provided at runtime per request.
Here is how to create an instance of `QuestionAnswerAdvisor` where the threshold is `0.8` and to return the top `6` results.
```
var qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
        .searchRequest(SearchRequest.builder().similarityThreshold(0.8d).topK(6).build())
        .build();
Copied!

```

####  Dynamic Filter Expressions
Update the `SearchRequest` filter expression at runtime using the `FILTER_EXPRESSION` advisor context parameter:
```
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore)
        .searchRequest(SearchRequest.builder().build())
        .build())
    .build();

// Update filter expression at runtime
String content = this.chatClient.prompt()
    .user("Please answer my question XYZ")
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "type == 'Spring'"))
    .call()
    .content();
Copied!

```

The `FILTER_EXPRESSION` parameter allows you to dynamically filter the search results based on the provided expression.
####  Custom Template
The `QuestionAnswerAdvisor` uses a default template to augment the user question with the retrieved documents. You can customize this behavior by providing your own `PromptTemplate` object via the `.promptTemplate()` builder method.
The `PromptTemplate` provided here customizes how the advisor merges retrieved context with the user query. This is distinct from configuring a `TemplateRenderer` on the `ChatClient` itself (using `.templateRenderer()`), which affects the rendering of the initial user/system prompt content **before** the advisor runs. See [ChatClient Prompt Templates](https://docs.spring.io/spring-ai/reference/api/chatclient.html#_prompt_templates) for more details on client-level template rendering.   
---  
Th

[Content truncated...]