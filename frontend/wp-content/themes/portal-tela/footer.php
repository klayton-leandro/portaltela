</main>

<footer class="footer bg-dark text-light py-4 mt-auto">
  <div class="container">
    <div class="row align-items-center">
      <div class="col-md-6 text-center text-md-start">
        <h6 class="text-white mb-2">
          <?php bloginfo('name'); ?>
        </h6>
        <p class="text-white mb-0 small">
          &copy; <?php echo date('Y'); ?>. Todos os direitos reservados.
        </p>
      </div>
      <div class="col-md-6 text-center text-md-end mt-3 mt-md-0">
        <a href="<?php bloginfo('rss2_url'); ?>" class="text-white me-3" aria-label="RSS">
          <i class="bi bi-rss fs-6"></i>
        </a>
        <a href="#" class="text-white me-3" aria-label="Facebook">
          <i class="bi bi-facebook fs-6"></i>
        </a>
        <a href="#" class="text-white" aria-label="Instagram">
          <i class="bi bi-instagram fs-6"></i>
        </a>
      </div>
    </div>
  </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
