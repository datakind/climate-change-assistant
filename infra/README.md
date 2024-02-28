# @probable-futures/infra

AWS Infrastructure is managed by [Pulumi](https://www.pulumi.com/). In order to access Pulumi configuration and secrets, you'll need access to the Pulumi account.

GitHub Actions will preview infrastructure changes on pull request, and apply
them automatically on merges to main and production branches. Each branch deploys to its corresponding stack.
