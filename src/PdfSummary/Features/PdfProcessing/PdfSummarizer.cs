using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace PdfSummary.Features.PdfProcessing
{
    public class PdfSummarizer : IPdfSummarizer
    {
        public async Task<string> SummarizeTextAsync(string text)
        {
            // For a real implementation, you would integrate with an AI service like OpenAI
            // This is a simplified implementation that extracts key sentences
            
            if (string.IsNullOrEmpty(text))
                return "No text to summarize.";

            // Simple extractive summarization
            var sentences = text.Split(new[] { '.', '!', '?' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(s => s.Trim())
                .Where(s => s.Length > 20)  // Filter out very short sentences
                .ToList();

            // Take first sentence, a middle sentence, and last sentence as a simple summary
            var summary = new StringBuilder();
            
            if (sentences.Count > 0)
                summary.AppendLine(sentences[0] + ".");
                
            if (sentences.Count > 2)
                summary.AppendLine(sentences[sentences.Count / 2] + ".");
                
            if (sentences.Count > 1)
                summary.AppendLine(sentences[sentences.Count - 1] + ".");

            return summary.ToString();
        }
    }
}
