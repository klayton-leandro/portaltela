<?php
/**
 * Plugin Name: Content Receiver
 * Description: Recebe conteúdo via webhook e cria posts automaticamente no WordPress.
 * Version: 1.0.0
 * Author: Klayton Leandro Matos de Paula
 * Text Domain: content-receiver
 */

if (!defined('ABSPATH')) {
    exit;
}

class ContentReceiverPlugin
{
    /**
     * Chave de autenticação para o webhook (pode ser configurada via admin)
     */
    private $api_key;

    /**
     * Construtor do plugin
     */
    public function __construct()
    {
        $this->api_key = get_option('content_receiver_api_key', '');
        
        // Registra o endpoint REST API
        add_action('rest_api_init', [$this, 'register_webhook_endpoint']);
        
        // Adiciona página de configurações no admin
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    /**
     * Registra o endpoint do webhook na REST API
     */
    public function register_webhook_endpoint()
    {
        register_rest_route('content-receiver/v1', '/webhook', [
            'methods'             => 'POST',
            'callback'            => [$this, 'handle_webhook'],
            'permission_callback' => [$this, 'verify_request'],
        ]);
    }

    /**
     * Verifica a autenticação da requisição
     * 
     * @param WP_REST_Request $request
     * @return bool|WP_Error
     */
    public function verify_request(WP_REST_Request $request)
    {
        // Obtém a chave da API do header ou do corpo da requisição
        $provided_key = $request->get_header('X-API-Key');
        
        if (empty($provided_key)) {
            $provided_key = $request->get_param('api_key');
        }

        // Se não houver chave configurada, permite acesso (para desenvolvimento)
        if (empty($this->api_key)) {
            return true;
        }

        // Verifica se a chave fornecida corresponde à configurada
        if ($provided_key !== $this->api_key) {
            return new WP_Error(
                'unauthorized',
                'Chave de API inválida ou não fornecida.',
                ['status' => 401]
            );
        }

        return true;
    }

    /**
     * Processa a requisição do webhook e cria o post
     * 
     * @param WP_REST_Request $request
     * @return WP_REST_Response|WP_Error
     */
    public function handle_webhook(WP_REST_Request $request)
    {
        $params = $request->get_json_params();

        // Validação dos campos obrigatórios
        if (empty($params['title'])) {
            return new WP_Error(
                'missing_title',
                'O campo "title" é obrigatório.',
                ['status' => 400]
            );
        }

        if (empty($params['content'])) {
            return new WP_Error(
                'missing_content',
                'O campo "content" é obrigatório.',
                ['status' => 400]
            );
        }

        // Prepara os dados do post
        $post_data = [
            'post_title'   => sanitize_text_field($params['title']),
            'post_content' => wp_kses_post($params['content']),
            'post_status'  => isset($params['status']) ? sanitize_text_field($params['status']) : 'publish',
            'post_type'    => isset($params['post_type']) ? sanitize_text_field($params['post_type']) : 'post',
            'post_author'  => isset($params['author_id']) ? absint($params['author_id']) : 1,
        ];

        // Adiciona excerpt se fornecido
        if (!empty($params['excerpt'])) {
            $post_data['post_excerpt'] = sanitize_textarea_field($params['excerpt']);
        }

        // Adiciona data de publicação se fornecida
        if (!empty($params['date'])) {
            $post_data['post_date'] = sanitize_text_field($params['date']);
        }

        // Adiciona slug se fornecido
        if (!empty($params['slug'])) {
            $post_data['post_name'] = sanitize_title($params['slug']);
        }

        // Cria o post
        $post_id = wp_insert_post($post_data, true);

        if (is_wp_error($post_id)) {
            return new WP_Error(
                'post_creation_failed',
                'Falha ao criar o post: ' . $post_id->get_error_message(),
                ['status' => 500]
            );
        }

        // Adiciona categorias se fornecidas
        if (!empty($params['categories']) && is_array($params['categories'])) {
            $category_ids = [];
            foreach ($params['categories'] as $category) {
                // Pode ser ID ou nome da categoria
                if (is_numeric($category)) {
                    $category_ids[] = absint($category);
                } else {
                    // Tenta encontrar ou criar a categoria
                    $term = get_term_by('name', $category, 'category');
                    if ($term) {
                        $category_ids[] = $term->term_id;
                    } else {
                        $new_term = wp_insert_term($category, 'category');
                        if (!is_wp_error($new_term)) {
                            $category_ids[] = $new_term['term_id'];
                        }
                    }
                }
            }
            if (!empty($category_ids)) {
                wp_set_post_categories($post_id, $category_ids);
            }
        }

        // Adiciona tags se fornecidas
        if (!empty($params['tags']) && is_array($params['tags'])) {
            wp_set_post_tags($post_id, array_map('sanitize_text_field', $params['tags']));
        }

        // Adiciona imagem destacada se URL fornecida
        if (!empty($params['featured_image'])) {
            $image_url = $params['featured_image'];
            error_log('Content Receiver: featured_image recebido: ' . print_r($image_url, true));
            
            // Se for um array, pega a primeira imagem
            if (is_array($image_url)) {
                $image_url = !empty($image_url[0]) ? $image_url[0] : null;
                error_log('Content Receiver: featured_image era array, extraiu: ' . $image_url);
            }
            
            if (!empty($image_url) && is_string($image_url)) {
                error_log('Content Receiver: Tentando baixar imagem: ' . $image_url);
                $result = $this->set_featured_image_from_url($post_id, $image_url);
                error_log('Content Receiver: Resultado set_featured_image: ' . print_r($result, true));
            } else {
                error_log('Content Receiver: image_url vazio ou não é string');
            }
        } else {
            error_log('Content Receiver: featured_image não fornecido');
        }

        // Adiciona meta fields customizados se fornecidos
        if (!empty($params['meta']) && is_array($params['meta'])) {
            foreach ($params['meta'] as $meta_key => $meta_value) {
                update_post_meta($post_id, sanitize_key($meta_key), sanitize_text_field($meta_value));
            }
        }

        // Retorna resposta de sucesso
        return new WP_REST_Response([
            'success' => true,
            'message' => 'Post criado com sucesso.',
            'post_id' => $post_id,
            'post_url' => get_permalink($post_id),
        ], 201);
    }

    /**
     * Define a imagem destacada a partir de uma URL
     * 
     * @param int $post_id
     * @param string $image_url
     * @return int|false ID do attachment ou false em caso de erro
     */
    private function set_featured_image_from_url($post_id, $image_url)
    {
        require_once ABSPATH . 'wp-admin/includes/media.php';
        require_once ABSPATH . 'wp-admin/includes/file.php';
        require_once ABSPATH . 'wp-admin/includes/image.php';

        // Baixa a imagem e anexa ao post
        $attachment_id = media_sideload_image($image_url, $post_id, '', 'id');

        if (is_wp_error($attachment_id)) {
            error_log('Content Receiver: Falha ao baixar imagem - ' . $attachment_id->get_error_message());
            return false;
        }

        // Define como imagem destacada
        set_post_thumbnail($post_id, $attachment_id);

        return $attachment_id;
    }

    /**
     * Adiciona página de configurações no menu admin
     */
    public function add_admin_menu()
    {
        add_options_page(
            'Content Receiver',
            'Content Receiver',
            'manage_options',
            'content-receiver',
            [$this, 'render_settings_page']
        );
    }

    /**
     * Registra as configurações do plugin
     */
    public function register_settings()
    {
        register_setting('content_receiver_settings', 'content_receiver_api_key');

        add_settings_section(
            'content_receiver_main',
            'Configurações do Webhook',
            null,
            'content-receiver'
        );

        add_settings_field(
            'content_receiver_api_key',
            'Chave da API',
            [$this, 'render_api_key_field'],
            'content-receiver',
            'content_receiver_main'
        );
    }

    /**
     * Renderiza o campo da chave de API
     */
    public function render_api_key_field()
    {
        $api_key = get_option('content_receiver_api_key', '');
        ?>
        <input type="text" 
               name="content_receiver_api_key" 
               value="<?php echo esc_attr($api_key); ?>" 
               class="regular-text"
               placeholder="Deixe em branco para desabilitar autenticação">
        <p class="description">
            Esta chave deve ser enviada no header <code>X-API-Key</code> ou no campo <code>api_key</code> do payload.
        </p>
        <?php
    }

    /**
     * Renderiza a página de configurações
     */
    public function render_settings_page()
    {
        ?>
        <div class="wrap">
            <h1>Content Receiver - Configurações</h1>
            
            <form method="post" action="options.php">
                <?php
                settings_fields('content_receiver_settings');
                do_settings_sections('content-receiver');
                submit_button();
                ?>
            </form>

            <hr>

            <h2>Informações do Webhook</h2>
            
            <table class="form-table">
                <tr>
                    <th>URL do Endpoint:</th>
                    <td>
                        <code><?php echo esc_url(rest_url('content-receiver/v1/webhook')); ?></code>
                    </td>
                </tr>
                <tr>
                    <th>Método:</th>
                    <td><code>POST</code></td>
                </tr>
                <tr>
                    <th>Content-Type:</th>
                    <td><code>application/json</code></td>
                </tr>
            </table>

            <h3>Exemplo de Payload</h3>
            <pre style="background: #f1f1f1; padding: 15px; overflow-x: auto;">
{
    "title": "Título do Post",
    "content": "&lt;p&gt;Conteúdo HTML do post...&lt;/p&gt;",
    "excerpt": "Resumo do post (opcional)",
    "status": "publish",
    "categories": ["Tecnologia", "Notícias"],
    "tags": ["IA", "Automação"],
    "featured_image": "https://exemplo.com/imagem.jpg",
    "meta": {
        "fonte": "Portal Notícias",
        "autor_original": "João Silva"
    }
}
            </pre>

            <h3>Campos Disponíveis</h3>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>Campo</th>
                        <th>Tipo</th>
                        <th>Obrigatório</th>
                        <th>Descrição</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>title</code></td>
                        <td>string</td>
                        <td>Sim</td>
                        <td>Título do post</td>
                    </tr>
                    <tr>
                        <td><code>content</code></td>
                        <td>string</td>
                        <td>Sim</td>
                        <td>Conteúdo HTML do post</td>
                    </tr>
                    <tr>
                        <td><code>excerpt</code></td>
                        <td>string</td>
                        <td>Não</td>
                        <td>Resumo/descrição do post</td>
                    </tr>
                    <tr>
                        <td><code>status</code></td>
                        <td>string</td>
                        <td>Não</td>
                        <td>Status do post (publish, draft, pending). Padrão: publish</td>
                    </tr>
                    <tr>
                        <td><code>categories</code></td>
                        <td>array</td>
                        <td>Não</td>
                        <td>Lista de categorias (IDs ou nomes)</td>
                    </tr>
                    <tr>
                        <td><code>tags</code></td>
                        <td>array</td>
                        <td>Não</td>
                        <td>Lista de tags</td>
                    </tr>
                    <tr>
                        <td><code>featured_image</code></td>
                        <td>string</td>
                        <td>Não</td>
                        <td>URL da imagem destacada</td>
                    </tr>
                    <tr>
                        <td><code>slug</code></td>
                        <td>string</td>
                        <td>Não</td>
                        <td>Slug/permalink do post</td>
                    </tr>
                    <tr>
                        <td><code>date</code></td>
                        <td>string</td>
                        <td>Não</td>
                        <td>Data de publicação (formato: Y-m-d H:i:s)</td>
                    </tr>
                    <tr>
                        <td><code>author_id</code></td>
                        <td>int</td>
                        <td>Não</td>
                        <td>ID do autor WordPress. Padrão: 1</td>
                    </tr>
                    <tr>
                        <td><code>meta</code></td>
                        <td>object</td>
                        <td>Não</td>
                        <td>Meta fields customizados (chave: valor)</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <?php
    }
}

// Inicializa o plugin
new ContentReceiverPlugin();
