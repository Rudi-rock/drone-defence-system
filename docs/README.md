# GitHub Pages Documentation

This folder contains the GitHub Pages website for the Autonomous Drone Swarm Security System.

## Hosting

The website is automatically deployed to GitHub Pages and available at:
**https://Rudi-rock.github.io/drone-defence-system/**

## File Structure

- `index.html` - Main landing page with project showcase
- `_config.yml` - GitHub Pages configuration (Jekyll)

## Customization

### Change the site URL
Edit the repository settings in GitHub:
1. Go to Settings → Pages
2. Configure the source (currently set to `docs/` folder)
3. Add custom domain if desired

### Modify Content
Edit `index.html` directly to customize sections, colors, and content.

## Local Testing

To test locally before pushing:

```bash
# Using Python's simple HTTP server
python -m http.server 3000

# Then visit: http://localhost:3000
```

## Publishing

Changes to this folder are automatically published to GitHub Pages when pushed to the `main` branch.

```bash
git add docs/
git commit -m "Update GitHub Pages content"
git push origin main
```

The site should update within 1-2 minutes.
