const std = @import("std");

// main関数はwant構造体を受け取り、hashmapを利用したグラフAPI関数を提供します。
pub fn main() {};


const WantId = enum {
    USER_REGISTRATION,
    VALIDATE_USERNAME,
    CHECK_USERNAME_LENGTH,
    USER,

    pub fn fromString(str: []const u8) !WantId {
        return std.meta.stringToEnum(WantId, str) orelse return error.InvalidWantId;
    }
};

const Want = struct {
    id: WantId,
    description: []const u8,
    sub_wants: []const WantId,
    related_types: []const []const u8,
};

const WantData = struct {
    id: WantId,
    description: []const u8,
};

fn createWantFromData(allocator: std.mem.Allocator, data: WantData) !*Want {
    const want = try allocator.create(Want);
    want.* = .{
        .id = data.id,
        .description = data.description,
        .sub_wants = &[_]WantId{},
        .related_types = &[_][]const u8{},
    };
    return want;
}

test "wantのテスト" {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var want_map = std.AutoHashMap(WantId, *Want).init(allocator);
    defer {
        // マップ内の各Wantを解放
        var it = want_map.valueIterator();
        while (it.next()) |want_ptr| {
            allocator.destroy(want_ptr.*);
        }
        // マップ自体を解放
        want_map.deinit();
    }

    for (want_data_list) |data| {
        const want_ptr = try createWantFromData(allocator, data);
        try want_map.put(want_ptr.id, want_ptr);
    }

    // テスト用の出力
    if (want_map.get(WantId.USER_REGISTRATION)) |want_ptr| {
        std.debug.print("Found want: {s}\n", .{want_ptr.description});
    }
    std.debug.print("Registered Want count: {d}\n", .{want_map.count()});
}

const want_data_list = [_]WantData{
    .{ .id = .USER_REGISTRATION, .description = "ユーザー登録処理全体を実行したい" },
    .{ .id = .VALIDATE_USERNAME, .description = "ユーザー名をバリデーションしたい" },
    .{ .id = .CHECK_USERNAME_LENGTH, .description = "ユーザー名の長さをチェックしたい" },
    .{ .id = .USER, .description = "アプリケーション全体でユーザー情報を一元管理したい" },
};
