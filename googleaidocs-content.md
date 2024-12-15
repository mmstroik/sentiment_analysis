Generating content  |  Gemini API  |  Google AI for Developers
==================


Method: models.generateContent
------------------------------

Generates a model response given an input `GenerateContentRequest`.

### Endpoint

post https://generativelanguage.googleapis.com/v1beta/{model=models/\*}:generateContent  

### Path parameters

`model` `string`

Required. The name of the `Model` to use for generating the completion.

Format: `name=models/{model}`. It takes the form `models/{model}`.

### Request body

The request body contains data with the following structure:

Fields

`contents[]` ``object (`[Content](https://ai.google.dev/api/caching#Content)`)``

Required. The content of the current conversation with the model.

For single-turn queries, this is a single instance. For multi-turn queries like [chat](https://ai.google.dev/gemini-api/docs/text-generation#chat), this is a repeated field that contains the conversation history and the latest request.

`tools[]` ``object (`[Tool](https://ai.google.dev/api/caching#Tool)`)``

Optional. A list of `Tools` the `Model` may use to generate the next response.

A `Tool` is a piece of code that enables the system to interact with external systems to perform an action, or set of actions, outside of knowledge and scope of the `Model`. Supported `Tool`s are `Function` and `codeExecution`. Refer to the [Function calling](https://ai.google.dev/gemini-api/docs/function-calling) and the [Code execution](https://ai.google.dev/gemini-api/docs/code-execution) guides to learn more.

`toolConfig` ``object (`[ToolConfig](https://ai.google.dev/api/caching#ToolConfig)`)``

Optional. Tool configuration for any `Tool` specified in the request. Refer to the [Function calling guide](https://ai.google.dev/gemini-api/docs/function-calling#function_calling_mode) for a usage example.

`safetySettings[]` ``object (`[SafetySetting](https://ai.google.dev/api/generate-content#v1beta.SafetySetting)`)``

Optional. A list of unique `SafetySetting` instances for blocking unsafe content.

This will be enforced on the `GenerateContentRequest.contents` and `GenerateContentResponse.candidates`. There should not be more than one setting for each `SafetyCategory` type. The API will block any contents and responses that fail to meet the thresholds set by these settings. This list overrides the default settings for each `SafetyCategory` specified in the safetySettings. If there is no `SafetySetting` for a given `SafetyCategory` provided in the list, the API will use the default safety setting for that category. Harm categories HARM\_CATEGORY\_HATE\_SPEECH, HARM\_CATEGORY\_SEXUALLY\_EXPLICIT, HARM\_CATEGORY\_DANGEROUS\_CONTENT, HARM\_CATEGORY\_HARASSMENT are supported. Refer to the [guide](https://ai.google.dev/gemini-api/docs/safety-settings) for detailed information on available safety settings. Also refer to the [Safety guidance](https://ai.google.dev/gemini-api/docs/safety-guidance) to learn how to incorporate safety considerations in your AI applications.

`systemInstruction` ``object (`[Content](https://ai.google.dev/api/caching#Content)`)``

Optional. Developer set [system instruction(s)](https://ai.google.dev/gemini-api/docs/system-instructions). Currently, text only.

`generationConfig` ``object (`[GenerationConfig](https://ai.google.dev/api/generate-content#v1beta.GenerationConfig)`)``

Optional. Configuration options for model generation and outputs.

`cachedContent` `string`

Optional. The name of the content [cached](https://ai.google.dev/gemini-api/docs/caching) to use as context to serve the prediction. Format: `cachedContents/{cachedContent}`

# Example request

## Text

### Python

```
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Write a story about a magic backpack.")
print(response.text)text_generation.py
```

### Shell

```
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[{"text": "Write a story about a magic backpack."}]
        }]
       }' 2> /dev/nulltext_generation.sh
```

## Generation Config

### Python

```
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(
    "Tell me a story about a magic backpack.",
    generation_config=genai.types.GenerationConfig(
        # Only one candidate for now.
        candidate_count=1,
        stop_sequences=["x"],
        max_output_tokens=20,
        temperature=1.0,
    ),
)

print(response.text)configure_model_parameters.py
```

### Shell

```
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
        "contents": [{
            "parts":[
                {"text": "Write a story about a magic backpack."}
            ]
        }],
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ],
        "generationConfig": {
            "stopSequences": [
                "Title"
            ],
            "temperature": 1.0,
            "maxOutputTokens": 800,
            "topP": 0.8,
            "topK": 10
        }
    }'  2> /dev/null | grep "text"configure_model_parameters.sh
```

## System Instruction

### Python

```
import google.generativeai as genai

model = genai.GenerativeModel(
    "models/gemini-1.5-flash",
    system_instruction="You are a cat. Your name is Neko.",
)
response = model.generate_content("Good morning! How are you?")
print(response.text)system_instruction.py
```

### Shell

```
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
-H 'Content-Type: application/json' \
-d '{ "system_instruction": {
    "parts":
      { "text": "You are a cat. Your name is Neko."}},
    "contents": {
      "parts": {
        "text": "Hello there"}}}'system_instruction.sh
```

## Response body

If successful, the response body contains an instance of `[GenerateContentResponse](https://ai.google.dev/api/generate-content#v1beta.GenerateContentResponse)`.


GenerateContentResponse
-----------------------

Response from the model supporting multiple candidate responses.

Safety ratings and content filtering are reported for both prompt in `GenerateContentResponse.prompt_feedback` and for each candidate in `finishReason` and in `safetyRatings`. The API: - Returns either all requested candidates or none of them - Returns no candidates at all only if there was something wrong with the prompt (check `promptFeedback`) - Reports feedback on each candidate in `finishReason` and `safetyRatings`.

Fields

`candidates[]` ``object (`[Candidate](https://ai.google.dev/api/generate-content#v1beta.Candidate)`)``

Candidate responses from the model.

`promptFeedback` ``object (`[PromptFeedback](https://ai.google.dev/api/generate-content#PromptFeedback)`)``

Returns the prompt's feedback related to the content filters.

`usageMetadata` ``object (`[UsageMetadata](https://ai.google.dev/api/generate-content#UsageMetadata)`)``

Output only. Metadata on the generation requests' token usage.

| JSON representation |
| --- |
| 
{
  "candidates": \[
    {
      object (`[Candidate](https://ai.google.dev/api/generate-content#v1beta.Candidate)`)
    }
  \],
  "promptFeedback": {
    object (`[PromptFeedback](https://ai.google.dev/api/generate-content#PromptFeedback)`)
  },
  "usageMetadata": {
    object (`[UsageMetadata](https://ai.google.dev/api/generate-content#UsageMetadata)`)
  }
}

 |


Candidate
---------


A response candidate generated from the model.

Fields

`content` ``object (`[Content](https://ai.google.dev/api/caching#Content)`)``

Output only. Generated content returned from the model.

`finishReason` ``enum (`[FinishReason](https://ai.google.dev/api/generate-content#FinishReason)`)``

Optional. Output only. The reason why the model stopped generating tokens.

If empty, the model has not stopped generating tokens.

`safetyRatings[]` ``object (`[SafetyRating](https://ai.google.dev/api/generate-content#v1beta.SafetyRating)`)``

List of ratings for the safety of a response candidate.

There is at most one rating per category.

`citationMetadata` ``object (`[CitationMetadata](https://ai.google.dev/api/generate-content#v1beta.CitationMetadata)`)``

Output only. Citation information for model-generated candidate.

This field may be populated with recitation information for any text included in the `content`. These are passages that are "recited" from copyrighted material in the foundational LLM's training data.

`tokenCount` `integer`

Output only. Token count for this candidate.

`groundingAttributions[]` ``object (`[GroundingAttribution](https://ai.google.dev/api/generate-content#GroundingAttribution)`)``

Output only. Attribution information for sources that contributed to a grounded answer.

This field is populated for `GenerateAnswer` calls.

`groundingMetadata` ``object (`[GroundingMetadata](https://ai.google.dev/api/generate-content#GroundingMetadata)`)``

Output only. Grounding metadata for the candidate.

This field is populated for `GenerateContent` calls.

`avgLogprobs` `number`

Output only.

`logprobsResult` ``object (`[LogprobsResult](https://ai.google.dev/api/generate-content#LogprobsResult)`)``

Output only. Log-likelihood scores for the response tokens and top tokens

`index` `integer`

Output only. Index of the candidate in the list of response candidates.

| JSON representation |
| --- |
| 
{
  "content": {
    object (`[Content](https://ai.google.dev/api/caching#Content)`)
  },
  "finishReason": enum (`[FinishReason](https://ai.google.dev/api/generate-content#FinishReason)`),
  "safetyRatings": \[
    {
      object (`[SafetyRating](https://ai.google.dev/api/generate-content#v1beta.SafetyRating)`)
    }
  \],
  "citationMetadata": {
    object (`[CitationMetadata](https://ai.google.dev/api/generate-content#v1beta.CitationMetadata)`)
  },
  "tokenCount": integer,
  "groundingAttributions": \[
    {
      object (`[GroundingAttribution](https://ai.google.dev/api/generate-content#GroundingAttribution)`)
    }
  \],
  "groundingMetadata": {
    object (`[GroundingMetadata](https://ai.google.dev/api/generate-content#GroundingMetadata)`)
  },
  "avgLogprobs": number,
  "logprobsResult": {
    object (`[LogprobsResult](https://ai.google.dev/api/generate-content#LogprobsResult)`)
  },
  "index": integer
}

 |


LogprobsResult
--------------

Logprobs Result

Fields

`topCandidates[]` ``object (`[TopCandidates](https://ai.google.dev/api/generate-content#TopCandidates)`)``

Length = total number of decoding steps.

`chosenCandidates[]` ``object (`[Candidate](https://ai.google.dev/api/generate-content#Candidate)`)``

Length = total number of decoding steps. The chosen candidates may or may not be in topCandidates.

| JSON representation |
| --- |
| 
{
  "topCandidates": \[
    {
      object (`[TopCandidates](https://ai.google.dev/api/generate-content#TopCandidates)`)
    }
  \],
  "chosenCandidates": \[
    {
      object (`[Candidate](https://ai.google.dev/api/generate-content#Candidate)`)
    }
  \]
}

 |

TopCandidates
-------------

Candidates with top log probabilities at each decoding step.

Fields

`candidates[]` ``object (`[Candidate](https://ai.google.dev/api/generate-content#Candidate)`)``

Sorted by log probability in descending order.

| JSON representation |
| --- |
| 
{
  "candidates": \[
    {
      object (`[Candidate](https://ai.google.dev/api/generate-content#Candidate)`)
    }
  \]
}

 |

Candidate
---------

Candidate for the logprobs token and score.

Fields

`token` `string`

The candidate’s token string value.

`tokenId` `integer`

The candidate’s token id value.

`logProbability` `number`

The candidate's log probability.

| JSON representation |
| --- |
| 
{
  "token": string,
  "tokenId": integer,
  "logProbability": number
}

 |

GenerationConfig
----------------

Configuration options for model generation and outputs. Not all parameters are configurable for every model.

Fields

`stopSequences[]` `string`

Optional. The set of character sequences (up to 5) that will stop output generation. If specified, the API will stop at the first appearance of a `stop_sequence`. The stop sequence will not be included as part of the response.

`responseMimeType` `string`

Optional. MIME type of the generated candidate text. Supported MIME types are: `text/plain`: (default) Text output. `application/json`: JSON response in the response candidates. `text/x.enum`: ENUM as a string response in the response candidates. Refer to the [docs](https://ai.google.dev/gemini-api/docs/prompting_with_media#plain_text_formats) for a list of all supported text MIME types.

`responseSchema` ``object (`[Schema](https://ai.google.dev/api/caching#Schema)`)``

Optional. Output schema of the generated candidate text. Schemas must be a subset of the [OpenAPI schema](https://spec.openapis.org/oas/v3.0.3#schema) and can be objects, primitives or arrays.

If set, a compatible `responseMimeType` must also be set. Compatible MIME types: `application/json`: Schema for JSON response. Refer to the [JSON text generation guide](https://ai.google.dev/gemini-api/docs/json-mode) for more details.

`candidateCount` `integer`

Optional. Number of generated responses to return.

Currently, this value can only be set to 1. If unset, this will default to 1.

`maxOutputTokens` `integer`

Optional. The maximum number of tokens to include in a response candidate.

Note: The default value varies by model, see the `Model.output_token_limit` attribute of the `Model` returned from the `getModel` function.

`temperature` `number`

Optional. Controls the randomness of the output.

Note: The default value varies by model, see the `Model.temperature` attribute of the `Model` returned from the `getModel` function.

Values can range from \[0.0, 2.0\].

`topP` `number`

Optional. The maximum cumulative probability of tokens to consider when sampling.

The model uses combined Top-k and Top-p (nucleus) sampling.

Tokens are sorted based on their assigned probabilities so that only the most likely tokens are considered. Top-k sampling directly limits the maximum number of tokens to consider, while Nucleus sampling limits the number of tokens based on the cumulative probability.

Note: The default value varies by `Model` and is specified by the`Model.top_p` attribute returned from the `getModel` function. An empty `topK` attribute indicates that the model doesn't apply top-k sampling and doesn't allow setting `topK` on requests.

`topK` `integer`

Optional. The maximum number of tokens to consider when sampling.

Gemini models use Top-p (nucleus) sampling or a combination of Top-k and nucleus sampling. Top-k sampling considers the set of `topK` most probable tokens. Models running with nucleus sampling don't allow topK setting.

Note: The default value varies by `Model` and is specified by the`Model.top_p` attribute returned from the `getModel` function. An empty `topK` attribute indicates that the model doesn't apply top-k sampling and doesn't allow setting `topK` on requests.

`presencePenalty` `number`

Optional. Presence penalty applied to the next token's logprobs if the token has already been seen in the response.

This penalty is binary on/off and not dependant on the number of times the token is used (after the first). Use `[frequencyPenalty](https://ai.google.dev/api/generate-content#FIELDS.frequency_penalty)` for a penalty that increases with each use.

A positive penalty will discourage the use of tokens that have already been used in the response, increasing the vocabulary.

A negative penalty will encourage the use of tokens that have already been used in the response, decreasing the vocabulary.

`frequencyPenalty` `number`

Optional. Frequency penalty applied to the next token's logprobs, multiplied by the number of times each token has been seen in the respponse so far.

A positive penalty will discourage the use of tokens that have already been used, proportional to the number of times the token has been used: The more a token is used, the more dificult it is for the model to use that token again increasing the vocabulary of responses.

Caution: A _negative_ penalty will encourage the model to reuse tokens proportional to the number of times the token has been used. Small negative values will reduce the vocabulary of a response. Larger negative values will cause the model to start repeating a common token until it hits the `[maxOutputTokens](https://ai.google.dev/api/generate-content#FIELDS.max_output_tokens)` limit: "...the the the the the...".

`responseLogprobs` `boolean`

Optional. If true, export the logprobs results in response.

`logprobs` `integer`

Optional. Only valid if `[responseLogprobs=True](https://ai.google.dev/api/generate-content#FIELDS.response_logprobs)`. This sets the number of top logprobs to return at each decoding step in the `[Candidate.logprobs_result](https://ai.google.dev/api/generate-content#FIELDS.logprobs_result)`.

| JSON representation |
| --- |
| 
{
  "stopSequences": \[
    string
  \],
  "responseMimeType": string,
  "responseSchema": {
    object (`[Schema](https://ai.google.dev/api/caching#Schema)`)
  },
  "candidateCount": integer,
  "maxOutputTokens": integer,
  "temperature": number,
  "topP": number,
  "topK": integer,
  "presencePenalty": number,
  "frequencyPenalty": number,
  "responseLogprobs": boolean,
  "logprobs": integer
}

 |
