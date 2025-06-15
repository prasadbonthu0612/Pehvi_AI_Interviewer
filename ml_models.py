import asyncio
from transformers import T5Tokenizer, AutoTokenizer
import language_tool_python as ltp
import pandas as pd
import onnxruntime as ort
from typing import List, Tuple, Optional
import numpy as np
import os

class InterviewModels:
    def __init__(self):
        print('Initializing LanguageTool...')
        self.tool = ltp.LanguageTool('en-US')
        print('LanguageTool initialized.')
        
        print('Setting up question model paths...')
        self.question_model_dir = "models/question_model.onnx"
        self.question_encoder_path = os.path.join(self.question_model_dir, "encoder_model.onnx")
        self.question_decoder_path = os.path.join(self.question_model_dir, "decoder_model.onnx")
        print('Loading question encoder...')
        self.question_encoder_session = ort.InferenceSession(self.question_encoder_path)
        print('Loading question decoder...')
        self.question_decoder_session = ort.InferenceSession(self.question_decoder_path)
        print('Loading question tokenizer...')
        self.question_tokenizer = T5Tokenizer.from_pretrained("t5-base")
        print('Question model and tokenizer loaded.')
        
        print('Setting up answer model paths...')
        self.answer_model_dir = "models/answering_model.onnx"
        self.answer_encoder_path = os.path.join(self.answer_model_dir, "encoder_model.onnx")
        self.answer_decoder_path = os.path.join(self.answer_model_dir, "decoder_model.onnx")
        print('Loading answer encoder...')
        self.answer_encoder_session = ort.InferenceSession(self.answer_encoder_path)
        print('Loading answer decoder...')
        self.answer_decoder_session = ort.InferenceSession(self.answer_decoder_path)
        print('Loading answer tokenizer...')
        self.answer_tokenizer = AutoTokenizer.from_pretrained("t5-base")
        print('Answer model and tokenizer loaded.')
        
        print('Loading dataset (CSV)...')
        self.dataset = pd.read_csv("data/python_developer_dataset.csv")
        self.dataset = self.dataset[self.dataset["Context Paragraph"].notnull()]
        print('Dataset loaded.')

    def get_context(self, job_role: str, difficulty: str) -> Optional[str]:
        """Get context based on job role and difficulty"""
        filtered_df = self.dataset[
            (self.dataset["Job Role"].str.lower() == job_role.lower()) &
            (self.dataset["Difficulty"].str.lower() == difficulty.lower())
        ]
        if filtered_df.empty:
            print("No context found for job_role={} and difficulty={}.".format(job_role, difficulty))
            return None
        context = filtered_df.sample(n=1)["Context Paragraph"].iloc[0]
        print("Context (for job_role={}, difficulty={}): {}".format(job_role, difficulty, context))
        return context

    def sample_next_token(self, logits, temperature=1.0, top_k=0, top_p=0.0):
        logits = logits / temperature
        logits = logits - np.max(logits)  # for numerical stability
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        sorted_indices = np.argsort(probs)[::-1]
        sorted_probs = probs[sorted_indices]
        if top_k > 0:
            sorted_indices = sorted_indices[:top_k]
            sorted_probs = sorted_probs[:top_k]
            sorted_probs = sorted_probs / np.sum(sorted_probs)
        if top_p > 0.0:
            cumulative_probs = np.cumsum(sorted_probs)
            cutoff = np.searchsorted(cumulative_probs, top_p) + 1
            sorted_indices = sorted_indices[:cutoff]
            sorted_probs = sorted_probs[:cutoff]
            sorted_probs = sorted_probs / np.sum(sorted_probs)
        next_token = np.random.choice(sorted_indices, p=sorted_probs)
        return next_token

    def check_grammar(self, generated_questions):
        scored = []
        for question in generated_questions:
            mistakes = len(self.tool.check(question))
            scored.append((question, mistakes))
        scored.sort(key=lambda x: x[1])  # Sort by number of mistakes
        return scored[0][0]

    def generate_questions_prompt(self, context: str) -> str:
        """Return a refined prompt for generating clear, well-defined technical interview questions."""
        prompt_prefix = (
            "Generate a clear, well-defined, and technical interview question for a candidate applying for the following role and difficulty. "
            "The question should be specific, unambiguous, and relevant to the context. Avoid vague or generic wording. "
            "Context: "
        )
        return prompt_prefix + context

    async def generate_questions(self, context: str, num_questions: int = 1, max_length: int = 32, temperature: float = 1.0, top_k: int = 40, top_p: float = 0.9, fast_mode: bool = True, num_beams: int = 3) -> str:
        """Generate questions asynchronously using ONNX. Fast mode uses greedy decoding for speed. Otherwise, use beam search."""
        input_text = self.generate_questions_prompt(context)
        input_ids = self.question_tokenizer.encode(input_text, return_tensors="np", add_special_tokens=True)
        attention_mask = np.ones_like(input_ids)
        encoder_outputs = self.question_encoder_session.run(
            None,
            {"input_ids": input_ids, "attention_mask": attention_mask}
        )
        encoder_hidden_states = encoder_outputs[0]
        if fast_mode:
            # Greedy decoding (as before)
            decoder_input_ids = np.array([[self.question_tokenizer.pad_token_id]], dtype=np.int64)
            generated_ids = []
            for _ in range(max_length):
                decoder_outputs = self.question_decoder_session.run(
                    None,
                    {
                        "input_ids": decoder_input_ids,
                        "encoder_hidden_states": encoder_hidden_states,
                        "encoder_attention_mask": attention_mask
                    }
                )
                next_token_logits = decoder_outputs[0][:, -1, :].squeeze()
                next_token_id = int(np.argmax(next_token_logits))
                generated_ids.append(next_token_id)
                if next_token_id == self.question_tokenizer.eos_token_id:
                    break
                decoder_input_ids = np.concatenate([decoder_input_ids, np.array([[next_token_id]], dtype=np.int64)], axis=-1)
            question = self.question_tokenizer.decode(generated_ids, skip_special_tokens=True)
            return question
        else:
            # Beam search
            beams = [
                {"ids": [self.question_tokenizer.pad_token_id], "score": 0.0, "ended": False}
                for _ in range(num_beams)
            ]
            beams[0]["score"] = 0.0  # The first beam is the main one
            for _ in range(max_length):
                all_candidates = []
                for beam in beams:
                    if beam["ended"]:
                        all_candidates.append(beam)
                        continue
                    decoder_input_ids = np.array([beam["ids"]], dtype=np.int64)
                    decoder_outputs = self.question_decoder_session.run(
                        None,
                        {
                            "input_ids": decoder_input_ids,
                            "encoder_hidden_states": encoder_hidden_states,
                            "encoder_attention_mask": attention_mask
                        }
                    )
                    next_token_logits = decoder_outputs[0][:, -1, :].squeeze()
                    next_token_logprobs = np.log_softmax(next_token_logits, axis=-1)
                    top_indices = np.argsort(next_token_logprobs)[-num_beams:][::-1]
                    for idx in top_indices:
                        candidate = {
                            "ids": beam["ids"] + [int(idx)],
                            "score": beam["score"] + float(next_token_logprobs[idx]),
                            "ended": (idx == self.question_tokenizer.eos_token_id)
                        }
                        all_candidates.append(candidate)
                # Keep top beams
                beams = sorted(all_candidates, key=lambda x: x["score"], reverse=True)[:num_beams]
                # If all beams ended, break
                if all(b["ended"] for b in beams):
                    break
            # Choose the best beam
            best_beam = max(beams, key=lambda x: x["score"])
            question = self.question_tokenizer.decode(best_beam["ids"], skip_special_tokens=True)
            return question

    def generate_answer_prompt(self, question: str) -> str:
        """Return a refined prompt for generating clear, well-structured technical answers."""
        return (
            "Provide a clear, detailed, and well-structured technical answer to the following interview question. "
            "Avoid repetition and incomplete sentences. Use examples if appropriate. Question: " + question
        )

    def postprocess_answer(self, answer: str) -> str:
        """Remove repeated phrases and ensure the answer ends with a complete sentence."""
        # Remove exact consecutive repetitions (simple approach)
        import re
        sentences = re.split(r'(?<=[.!?]) +', answer)
        seen = set()
        result = []
        for s in sentences:
            s_clean = s.strip().lower()
            if s_clean and s_clean not in seen:
                result.append(s.strip())
                seen.add(s_clean)
        # Join and ensure the answer ends with a period
        final = ' '.join(result).strip()
        if final and final[-1] not in '.!?':
            final += '.'
        return final

    async def generate_answer(self, question: str, max_length: int = 180, temperature: float = 0.7, top_k: int = 40, top_p: float = 0.9, fast_mode: bool = True, num_beams: int = 3) -> str:
        """Generate a detailed answer asynchronously using ONNX. Use beam search if not fast_mode."""
        input_text = self.generate_answer_prompt(question)
        inputs = self.answer_tokenizer(input_text, return_tensors="np", truncation=True)
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        encoder_outputs = self.answer_encoder_session.run(
            None,
            {"input_ids": input_ids, "attention_mask": attention_mask}
        )
        encoder_hidden_states = encoder_outputs[0]
        if fast_mode:
            decoder_input_ids = np.array([[self.answer_tokenizer.pad_token_id]], dtype=np.int64)
            generated_ids = []
            for _ in range(max_length):
                decoder_outputs = self.answer_decoder_session.run(
                    None,
                    {
                        "input_ids": decoder_input_ids,
                        "encoder_hidden_states": encoder_hidden_states,
                        "encoder_attention_mask": attention_mask
                    }
                )
                next_token_logits = decoder_outputs[0][:, -1, :].squeeze()
                next_token_id = int(np.argmax(next_token_logits))
                generated_ids.append(next_token_id)
                if next_token_id == self.answer_tokenizer.eos_token_id:
                    break
                decoder_input_ids = np.concatenate([decoder_input_ids, np.array([[next_token_id]], dtype=np.int64)], axis=-1)
            answer = self.answer_tokenizer.decode(generated_ids, skip_special_tokens=True)
        else:
            # Beam search
            beams = [
                {"ids": [self.answer_tokenizer.pad_token_id], "score": 0.0, "ended": False}
                for _ in range(num_beams)
            ]
            beams[0]["score"] = 0.0
            for _ in range(max_length):
                all_candidates = []
                for beam in beams:
                    if beam["ended"]:
                        all_candidates.append(beam)
                        continue
                    decoder_input_ids = np.array([beam["ids"]], dtype=np.int64)
                    decoder_outputs = self.answer_decoder_session.run(
                        None,
                        {
                            "input_ids": decoder_input_ids,
                            "encoder_hidden_states": encoder_hidden_states,
                            "encoder_attention_mask": attention_mask
                        }
                    )
                    next_token_logits = decoder_outputs[0][:, -1, :].squeeze()
                    next_token_logprobs = np.log_softmax(next_token_logits, axis=-1)
                    top_indices = np.argsort(next_token_logprobs)[-num_beams:][::-1]
                    for idx in top_indices:
                        candidate = {
                            "ids": beam["ids"] + [int(idx)],
                            "score": beam["score"] + float(next_token_logprobs[idx]),
                            "ended": (idx == self.answer_tokenizer.eos_token_id)
                        }
                        all_candidates.append(candidate)
                beams = sorted(all_candidates, key=lambda x: x["score"], reverse=True)[:num_beams]
                if all(b["ended"] for b in beams):
                    break
            best_beam = max(beams, key=lambda x: x["score"])
            answer = self.answer_tokenizer.decode(best_beam["ids"], skip_special_tokens=True)
        return self.postprocess_answer(answer)

    async def evaluate_answer(self, user_answer: str, model_answer: str) -> dict:
        """Evaluate user's answer against model's answer"""
        # TODO: Implement more sophisticated answer evaluation
        # For now, return a simple similarity score
        user_words = set(user_answer.lower().split())
        model_words = set(model_answer.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(user_words.intersection(model_words))
        union = len(user_words.union(model_words))
        similarity = intersection / union if union > 0 else 0
        
        feedback = {
            "similarity_score": round(similarity * 100, 2),
            "model_answer": model_answer,
            "feedback": self._generate_feedback(similarity)
        }
        return feedback

    def _generate_feedback(self, similarity: float) -> str:
        """Generate feedback based on similarity score"""
        if similarity >= 0.8:
            return "Excellent answer! You've covered most of the key points."
        elif similarity >= 0.6:
            return "Good answer! You've covered many important points, but could add more details."
        elif similarity >= 0.4:
            return "Fair answer. Consider adding more technical details and examples."
        else:
            return "Your answer could be improved. Consider reviewing the topic and providing more comprehensive coverage."

# Create a singleton instance
interview_models = InterviewModels()