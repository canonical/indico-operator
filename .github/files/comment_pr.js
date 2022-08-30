module.exports = async ({github, context}) => {
    const fs = require('fs');
    const report = JSON.parse(fs.readFileSync('./report.json'));
    const issue_number = report.number;
    const sha = report.sha;
    const createComment = async (body) => {
    await github.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: issue_number,
        body
    });
    }
    const coverageReport = report.reports.coverage.output.trim()
    if (!report.reports.lint.success) {
    const lintReport = report.reports.lint.output.trim();
    await createComment(`Lint checks failed for ${sha}\n\`\`\`\n${lintReport}\n\`\`\``);
    }
    if (!report.reports.unit.success) {
    const unitReport = report.reports.unit.output.trim();
    await createComment(`Unit tests failed for ${sha}\n\`\`\`\n${unitReport}\n\`\`\``);
    }
    await createComment(`Test coverage report for ${sha}\n\`\`\`\n${coverageReport}\n\`\`\``);
}
