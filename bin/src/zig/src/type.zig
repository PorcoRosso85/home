const std = @import("std");

const Meta = struct {
    description: []const u8,
};

const UserId = u64;

const User = struct {
    meta: Meta = .{ .description = "ユーザーを表す構造体" },
    id: UserId,
    name: []const u8,
};

const UserRegistrationResponse = struct {
    meta: Meta = .{
        .description = "ユーザー登録APIのレスポンス",
    },
    success: bool,
    message: []const u8,
    user: User,
};

fn printTypeInfo(comptime T: type) void {
    const type_name_ptr: [:0]const u8 = @typeName(T);
    const type_name: []const u8 = std.mem.sliceTo(type_name_ptr, 0);
    inline for (@typeInfo(T).Struct.fields) |field| {
        const field_type_info = @typeInfo(field.type);
        if (field_type_info == .Struct) {
            std.debug.print("{s}.{s} depends:-------\n", .{ type_name, field.name });
            printTypeInfo(field.type);
        } else {
            std.debug.print("{s}.{s} type: {s}\n", .{ type_name, field.name, @typeName(field.type) });
        }
    }
}

test "型出力_依存_再帰" {
    printTypeInfo(UserRegistrationResponse);
}

const UserProcessError = error{
    InvalidError,
    DatabaseError,
    NetworkError,
};

// UserRegistarationResponseとともに、失敗時にUserProcessErrorを発生する
const UserProcess = fn (User) UserProcessError!UserRegistrationResponse;

fn printTypeInfoError(comptime FuncType: type) void {
    const type_name = @typeName(FuncType);
    const fn_info = @typeInfo(FuncType).Fn;

    if (fn_info.return_type) |return_type| {
        const return_type_info = @typeInfo(return_type);
        if (return_type_info == .ErrorUnion) {
            std.debug.print("{s} return type error union cases:-------\n", .{type_name});

            const error_set_type = return_type_info.ErrorUnion.error_set;
            const error_set_info = @typeInfo(error_set_type);

            switch (error_set_info) {
                .ErrorSet => |error_set| {
                    std.debug.print("{any}\n", .{error_set});
                    // TODO ASCIIで表示される
                    if (error_set) |errors| {
                        inline for (errors) |err| {
                            std.debug.print("- {s}\n", .{err.name});
                        }
                    }
                },
                else => unreachable,
            }
        }
    } else {
        std.debug.print("{s} has no return type.\n", .{type_name});
    }
}

test "エラー型_関数型" {
    // printTypeInfoを拡張して printtypeinfoerror関数を作成し
    // 指定した関数型の引数型、返却型、エラー共用型について取得したい
    // TODO 何をイテレーションすればいいかデバッグ必要
    printTypeInfoError(UserProcess);
    // TODO
    // 関数型の中でUserRegister型で永続化処理がある, これは引数返却に現れていない
    // 現れてない実装内で依存する型も, reflectionやquatation, comptimeで取得可能？それとも引数返却エラーしか取れない？
    //
    // FIXME 関数型内の依存処理が抽出できるならいけるんだよ... 全部引数にするか？
}

test "高階型" {
    // 関数型が関数型を引数とできるか
}

const UserRegister = fn (User) void{};
const Auth = struct {};
const UserAuth = fn (UserRegister, Auth) void{};

// TODO
test "依存型" {}

test "要件まで拡張" {
    // 関数型が要件を守っているか
    // 関数型が要件を表現できるか
}
