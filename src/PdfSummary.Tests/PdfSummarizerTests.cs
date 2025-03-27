using System.Threading.Tasks;
using PdfSummary.Features.PdfProcessing;
using Xunit;

namespace PdfSummary.Tests
{
    public class PdfSummarizerTests
    {
        [Fact]
        public async Task SummarizeTextAsync_WithValidText_ReturnsSummary()
        {
            // Arrange
            var summarizer = new PdfSummarizer();
            var text = "This is the first sentence. This is a middle sentence with enough characters. This is the last sentence in the document.";

            // Act
            var result = await summarizer.SummarizeTextAsync(text);

            // Assert
            Assert.Contains("This is the first sentence", result);
            Assert.Contains("This is the last sentence", result);
        }

        [Fact]
        public async Task SummarizeTextAsync_WithEmptyText_ReturnsMessage()
        {
            // Arrange
            var summarizer = new PdfSummarizer();
            
            // Act
            var result = await summarizer.SummarizeTextAsync("");

            // Assert
            Assert.Equal("No text to summarize.", result);
        }
    }
}
