use bevy::prelude::*;

#[cfg(any(target_os = "android", target_os = "ios"))]
use bevy::ecs::{
    entity::Entity,
    system::{Commands, Query, SystemState},
};
#[cfg(any(target_os = "android", target_os = "ios"))]
use bevy::input::{keyboard::KeyboardInput, ButtonState};

#[cfg(any(target_os = "android", target_os = "ios"))]
mod app_view;

#[cfg(any(target_os = "android", target_os = "ios"))]
mod ffi;
#[cfg(any(target_os = "android", target_os = "ios"))]
pub use ffi::*;

#[cfg(target_os = "android")]
mod android_asset_io;

mod breakout;
#[allow(unused_variables)]
pub fn create_breakout_app(
    #[cfg(target_os = "android")] android_asset_manager: android_asset_io::AndroidAssetManager,
) -> App {
    #[allow(unused_imports)]
    use bevy::winit::WinitPlugin;
    use breakout::*;

    let mut bevy_app = App::new();

    #[allow(unused_mut)]
    let mut default_plugins = DefaultPlugins.build();

    // Temporary fix for the crash caused by winit on macOS Sonoma.
    #[cfg(target_os = "macos")]
    {
        default_plugins = default_plugins.set(WindowPlugin {
            primary_window: Some(Window {
                resolution: bevy::window::WindowResolution::new(900., 700.)
                    .with_scale_factor_override(2.0),
                resize_constraints: WindowResizeConstraints {
                    min_width: 600.,
                    min_height: 500.,
                    max_height: 1200.,
                    max_width: 1600.,
                },
                ..default()
            }),
            ..default()
        });
    }

    #[cfg(any(target_os = "android", target_os = "ios"))]
    {
        default_plugins = default_plugins
            .disable::<WinitPlugin>()
            .set(WindowPlugin::default());
    }

    #[cfg(target_os = "android")]
    {
        bevy_app.insert_non_send_resource(android_asset_manager);

        use bevy::render::{settings::WgpuSettings, RenderPlugin};
        default_plugins = default_plugins.set(RenderPlugin {
            wgpu_settings: WgpuSettings {
                backends: Some(wgpu::Backends::VULKAN),
                ..default()
            },
        });
        // the custom asset io plugin must be inserted in-between the
        // `CorePlugin' and `AssetPlugin`. It needs to be after the
        // CorePlugin, so that the IO task pool has already been constructed.
        // And it must be before the `AssetPlugin` so that the asset plugin
        // doesn't create another instance of an asset server. In general,
        // the AssetPlugin should still run so that other aspects of the
        // asset system are initialized correctly.
        default_plugins = default_plugins
            .add_before::<bevy::asset::AssetPlugin, _>(android_asset_io::AndroidAssetIoPlugin);
    }
    bevy_app
        .insert_resource(ClearColor(Color::rgb(0.8, 0.4, 0.6)))
        .add_plugins(default_plugins);

    #[cfg(any(target_os = "android", target_os = "ios"))]
    bevy_app.add_plugins(app_view::AppViewPlugin);

    bevy_app
        .insert_resource(Scoreboard { score: 0 })
        .insert_resource(ClearColor(BACKGROUND_COLOR))
        .add_systems(Startup, setup)
        .add_event::<CollisionEvent>()
        .add_systems(
            FixedUpdate,
            (
                check_for_collisions,
                apply_velocity.before(check_for_collisions),
                move_paddle
                    .before(check_for_collisions)
                    .after(apply_velocity),
                play_collision_sound.after(check_for_collisions),
            ),
        )
        .insert_resource(FixedTime::new_from_secs(TIME_STEP))
        .add_systems(Update, (update_scoreboard, bevy::window::close_on_esc));

    // In this scenario, need to call the setup() of the plugins that have been registered
    // in the App manually.
    // https://github.com/bevyengine/bevy/issues/7576
    // bevy 0.11 changed: https://github.com/bevyengine/bevy/pull/8336
    #[cfg(any(target_os = "android", target_os = "ios"))]
    {
        while !bevy_app.ready() {
            bevy::tasks::tick_global_task_pools_on_main_thread();
        }
        bevy_app.finish();
        bevy_app.cleanup();

        bevy_app.update();
    }

    bevy_app
}

#[cfg(any(target_os = "android", target_os = "ios"))]
pub(crate) fn change_input(app: &mut App, key_code: KeyCode, state: ButtonState) {
    let mut windows_system_state: SystemState<Query<(Entity, &mut Window)>> =
        SystemState::from_world(&mut app.world);
    let windows = windows_system_state.get_mut(&mut app.world);
    let (entity, _) = windows.get_single().unwrap();
    let input = KeyboardInput {
        scan_code: if key_code == KeyCode::Left { 123 } else { 124 },
        state,
        key_code: Some(key_code),
        window: entity,
    };
    app.world.cell().send_event(input);
}

#[cfg(any(target_os = "android", target_os = "ios"))]
pub(crate) fn close_bevy_window(mut app: Box<App>) {
    use bevy::app::AppExit;
    let mut windows_state: SystemState<(
        Commands,
        Query<(Entity, &mut Window)>,
        EventWriter<AppExit>,
    )> = SystemState::from_world(&mut app.world);
    let (mut commands, windows, mut app_exit_events) = windows_state.get_mut(&mut app.world);
    for (window, _focus) in windows.iter() {
        commands.entity(window).despawn();
    }
    app_exit_events.send(AppExit);
    windows_state.apply(&mut app.world);

    app.update();
}
